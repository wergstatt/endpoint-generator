from __future__ import annotations

from typing import Self
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import SQLTable, SQLPublic, SQLCreate


class ModelContainer(BaseModel):
    table: type[SQLTable]
    public: type[SQLPublic]
    create: type[SQLCreate]

    @classmethod
    def from_table(cls, table: type[SQLTable]) -> Self:
        public = [c for c in table.__bases__ if c.__name__.endswith("Public")][0]
        create = [c for c in public.__bases__ if c.__name__.endswith("Create")][0]
        return cls(table=table, public=public, create=create)


class ModelService:
    def __init__(self, table: type[SQLTable], session: AsyncSession):
        self.table = table
        self.session = session

        self.models = ModelContainer.from_table(table=self.table)

    async def create(self, data: SQLCreate) -> SQLTable:
        model = self.models.table(**data.model_dump())
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def read_all(self) -> Sequence[SQLTable]:
        stmt = select(self.models.table)
        return (await self.session.exec(stmt)).all()

    async def read(self, uuid: UUID) -> SQLTable | None:
        stmt = select(self.models.table).where(
            self.models.table.uuid == uuid,
        )
        return (await self.session.exec(stmt)).one_or_none()

    async def update(self, data: SQLPublic) -> SQLTable:
        model = await self.read(uuid=data.uuid)
        if model is None:
            raise HTTPException(status_code=404, detail="Model not found")
        model.sqlmodel_update(data.model_dump())
        self.session.add(model)
        await self.session.commit()
        return model

    async def delete(self, uuid: UUID) -> SQLTable:
        model = await self.read(uuid=uuid)
        await self.session.delete(model)
        await self.session.commit()
        return model
