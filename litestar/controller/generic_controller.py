from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from typing_extensions import get_args, get_origin
from litestar.handlers.http_handlers import get

from litestar.exceptions import ImproperlyConfiguredException, InvalidAnnotationException
from litestar.typing import FieldDefinition

from .base import Controller

if TYPE_CHECKING:
    from typing import Any


__all__ = ("GenericController",)

T = TypeVar("T")


class GenericController(Controller, Generic[T]):
    """Controller type that supports generic inheritance hierarchies."""

    model_type: type[T]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if not hasattr(cls, "model_type"):
            raise ImproperlyConfiguredException("a model_type attribute must be defined on generic controllers")

        super().__init_subclass__(**kwargs)

    def __init__(self, owner: Router) -> None:
        super().__init__(owner=owner)
        self.signature_namespace[T.__name__] = self.model_type
