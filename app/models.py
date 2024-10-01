from uuid import UUID

from sqlmodel import SQLModel, Field
from uuid_extensions import uuid7


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Mixins
class UUIDMixin(SQLModel):
    uuid: UUID = Field(
        default_factory=uuid7,
        primary_key=True,
        allow_mutation=False,
        unique=True,
    )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Create separate mixins for the standard models.
# This should allow to create a proper abstraction for the models.
class SQLCreate(SQLModel): ...


class SQLPublic(UUIDMixin): ...


class SQLTable(UUIDMixin): ...


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Models
class HeroCreate(SQLCreate):
    name: str
    secret_name: str


class HeroPublic(HeroCreate, SQLPublic): ...


class Hero(HeroPublic, SQLTable, table=True): ...
