from typing import Any, Generic, TypeVar

from litestar import delete, get, post, put
from litestar.contrib.repository.filters import LimitOffset
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.orm import DeclarativeBase

from .generic_controller import GenericController

T = TypeVar("T", bound=DeclarativeBase)
R = TypeVar("R", bound=SQLAlchemyAsyncRepository)


class GenericCRUDController(GenericController[T], Generic[T, R]):
    model_type: type[T]
    detail_route = "/{id:int}"

    @get("")
    async def list(self, repository: R) -> list[T]:
        return await repository.list()

    @get(detail_route)
    async def get(self, id: int, repository: R) -> T:
        return await repository.get(id)

    @post()
    async def create(self, data: T, repository: R) -> T:
        return await repository.add(data, auto_commit=True)

    @put(detail_route)
    async def update(self, id: int, data: T, repository: R) -> T:
        return await repository.update(
            {"id": id, **data},
            auto_commit=True,
        )

    @delete(detail_route, return_dto=None)
    async def delete(self, id: int, repository: R) -> None:
        await repository.delete(id, auto_commit=True)
