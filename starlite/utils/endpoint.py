from inspect import getfullargspec, isawaitable, signature
from typing import Any, Callable, Dict, List, Tuple, Union, cast

from pydantic import BaseModel, create_model
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from typing_extensions import Type

from starlite.decorators import RouteInfo
from starlite.enums import HttpMethod, MediaType
from starlite.response import Response


def parse_query_params(request: Request) -> Dict[str, Any]:
    """
    Parses and normalize a given request's query parameters into a regular dictionary

    supports list query params
    """
    params: Dict[str, Union[str, List[str]]] = {}
    for key, value in request.query_params.multi_items():
        current_params = params.get(key)
        if current_params:
            if isinstance(current_params, str):
                params[key] = [current_params, value]
            else:
                params[key] = [*cast(list, current_params), value]
        else:
            params[key] = value
    return params


def model_function_signature(function: Callable, annotations: Dict[str, Any]) -> Type[BaseModel]:

    """Creates a pydantic model from a given dictionary of type annotations"""

    method_signature = signature(function)
    field_definitions: Dict[str, Tuple[Any, Any]] = {}
    for key, value in annotations.items():
        parameter = method_signature.parameters[key]
        if parameter.default is not method_signature.empty:
            field_definitions[key] = (value, parameter.default)
        elif not repr(parameter.annotation).startswith("typing.Optional"):
            field_definitions[key] = (value, ...)
        else:
            field_definitions[key] = (value, None)
    return create_model("ParamModel", **field_definitions)


async def get_http_handler_parameters(function: Callable, request: Request) -> Dict[str, Any]:
    """
    Parse a given http handler function and return values matching function parameter keys
    """
    parameters: Dict[str, Any] = {}
    annotations = getfullargspec(function).annotations

    t_headers = annotations.pop("headers") if "headers" in annotations else None
    if t_headers:
        headers = dict(request.headers.items())
        if issubclass(t_headers, BaseModel):
            parameters["headers"] = t_headers(**headers)
        else:
            parameters["headers"] = headers
    t_data = annotations.pop("data") if "data" in annotations else None
    if t_data:
        # TODO: handle form data, stream etc.
        data = await request.json()
        if issubclass(t_data, BaseModel):
            parameters["data"] = t_data(**data)
        else:
            parameters["data"] = data
    return {
        **model_function_signature(function=function, annotations=annotations)(
            **parse_query_params(request=request), **request.path_params
        ).dict(),
        **parameters,
    }


async def handle_request(function: Callable, request: Request) -> Response:
    """
    Handles a given request by both calling the passed in function,
    and parsing the RouteInfo stored as an attribute on it.
    """
    route_info = cast(RouteInfo, getattr(function, "route_info"))
    response_class = route_info.response_class or Response

    params = await get_http_handler_parameters(function=function, request=request)
    data = function(**params)

    if isawaitable(data):
        data = await data

    if route_info.status_code:
        status_code = route_info.status_code
    elif route_info.http_method == HttpMethod.POST:
        status_code = HTTP_201_CREATED
    elif route_info.http_method == HttpMethod.DELETE:
        status_code = HTTP_204_NO_CONTENT
    else:
        status_code = HTTP_200_OK

    return response_class(
        content=data,
        headers=route_info.response_headers,
        status_code=status_code,
        media_type=route_info.media_type or MediaType.JSON,
    )
