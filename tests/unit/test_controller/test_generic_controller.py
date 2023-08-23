from __future__ import annotations

from dataclasses import asdict
from typing import Generic, TypeVar

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Annotated
from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.controller import GenericController
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import create_test_client
from litestar import get, post
from tests import VanillaDataClassPerson, VanillaDataClassPersonFactory

from litestar.dto import DTOConfig


def test_generic_controller() -> None:
    class GenericPersonController(GenericController[VanillaDataClassPerson]):
        model_type = VanillaDataClassPerson
        path = "/"

        @get("/{id:int}")
        def get_handler(self, id: int) -> VanillaDataClassPerson:
            return VanillaDataClassPersonFactory.build(id=id)

        @post("/")
        def post_handler(self, data: VanillaDataClassPerson) -> VanillaDataClassPerson:
            return VanillaDataClassPersonFactory.build(**asdict(data))

        @get("/")
        def get_collection_handler(self) -> list[VanillaDataClassPerson]:
            return VanillaDataClassPersonFactory.batch(5)

    with create_test_client(GenericPersonController) as client:
        response = client.get("/1")
        assert response.status_code == HTTP_200_OK
        assert response.json()

        response = client.post("/", json=asdict(VanillaDataClassPersonFactory.build()))
        assert response.status_code == HTTP_201_CREATED
        assert response.json()

        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert len(response.json()) == 5


def test_generic_sub_controller() -> None:
    T = TypeVar("T")

    class GenericSubController(GenericController[T], Generic[T]):
        model_type = T

        @get("/{id:int}")
        def get_handler(self, id: int) -> T:
            return VanillaDataClassPersonFactory.build(id=id)

    class GenericPersonController(GenericSubController[VanillaDataClassPerson]):
        model_type = VanillaDataClassPerson
        path = "/"

    with create_test_client(GenericPersonController) as client:
        response = client.get("/1")
        assert response.status_code == HTTP_200_OK
        assert response.json()


def test_generic_sub_controller_sqlalchemy() -> None:
    T = TypeVar("T")

    class GenericSubController(GenericController[T], Generic[T]):
        model_type = T

        @get("/{id:int}")
        def get_handler(self, id: int) -> T:
            return self.model_type(id=id)

    class Base(DeclarativeBase):
        pass

    class Person(Base):
        __tablename__ = "user"
        id: Mapped[int] = mapped_column(primary_key=True)

    PersonDTO = SQLAlchemyDTO[
        Annotated[
            Person,
            DTOConfig(rename_fields={"id": "ouid"}),
        ]
    ]

    class GenericPersonController(GenericSubController[Person]):
        model_type = Person
        dto = PersonDTO
        path = "/"

    with create_test_client(GenericPersonController) as client:
        response = client.get("/1")
        assert response.status_code == HTTP_200_OK
        assert response.json()["ouid"] == 1
