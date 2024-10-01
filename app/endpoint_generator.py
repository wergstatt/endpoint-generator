from typing import Self, Callable, Coroutine, Any
from uuid import UUID

import starlette.status as http_status
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app import models
from app.db import get_session
from app.model_service import ModelService, ModelContainer
from app.models import SQLTable, SQLCreate, SQLPublic

router = APIRouter()

ModelServiceFactory = Callable[[AsyncSession], Coroutine[Any, Any, ModelService]]


def get_model_service(table: type[SQLTable]) -> ModelServiceFactory:
    async def fn(session: AsyncSession = Depends(get_session)) -> ModelService:
        return ModelService(table=table, session=session)

    return fn


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Model Endpoint Configurations
class ModelEndpointConfig(BaseModel):
    path: str
    table: type[SQLTable]
    create: type[SQLCreate]
    response_model: type[SQLPublic]
    service: ModelServiceFactory

    @classmethod
    def from_table(cls, table: type[SQLTable]) -> Self:
        models_ = ModelContainer.from_table(table=table)
        return cls(
            path=f"/{models_.table.__tablename__}",
            table=models_.table,
            create=models_.create,
            response_model=models_.public,
            service=get_model_service(models_.table),
        )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Model Endpoint Templating Functions a.k.a Templation Island 🏝️
def add_create_model_endpoint(router_: APIRouter, config_: ModelEndpointConfig):
    @router_.post(
        path=config_.path,
        response_model=config_.response_model,
        status_code=http_status.HTTP_201_CREATED,
    )
    async def create(data: config_.create, service: ModelService = Depends(config_.service)):
        return await service.create(data=data)


def add_read_all_model_endpoint(router_: APIRouter, config_: ModelEndpointConfig):
    @router_.get(
        path=config_.path,
        response_model=list[config_.response_model],
        status_code=http_status.HTTP_200_OK,
    )
    async def read_all(service: ModelService = Depends(config_.service)):
        return await service.read_all()


def add_read_model_endpoint(router_: APIRouter, config_: ModelEndpointConfig):
    @router_.get(
        path=f"{config_.path}/{{uuid}}",
        response_model=config_.response_model,
        status_code=http_status.HTTP_200_OK,
    )
    async def read(uuid: UUID, service: ModelService = Depends(config_.service)):
        entity = await service.read(uuid=uuid)
        if entity is None:
            raise HTTPException(status_code=404, detail="Model not found")
        return entity


def add_update_model_endpoint(router_: APIRouter, config_: ModelEndpointConfig):
    @router_.patch(
        path=config_.path,
        response_model=config_.response_model,
        status_code=http_status.HTTP_200_OK,
    )
    async def update(
        data: config_.response_model, service: ModelService = Depends(config_.service)
    ):
        return await service.update(data=data)


def add_delete_model_endpoint(router_: APIRouter, config_: ModelEndpointConfig):
    @router_.delete(
        path=f"{config_.path}/{{uuid}}",
        response_model=config_.response_model,
        status_code=http_status.HTTP_200_OK,
    )
    async def delete(uuid: UUID, service: ModelService = Depends(config_.service)):
        return await service.delete(uuid=uuid)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Endpoint Creation 🛠️
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
model_endpoint_configs = [
    ModelEndpointConfig.from_table(table=models.Hero),
]

for config in model_endpoint_configs:
    add_create_model_endpoint(router, config)
    add_read_all_model_endpoint(router, config)
    add_read_model_endpoint(router, config)
    add_update_model_endpoint(router, config)
    add_delete_model_endpoint(router, config)
