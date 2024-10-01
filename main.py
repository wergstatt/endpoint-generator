from fastapi import FastAPI
from sqlmodel import SQLModel

from app.db import async_engine
from app.endpoint_generator import router

app = FastAPI(
    title="Endpoint Generator Sample",
    version="0.0.1",
    debug=True,
)
app.include_router(router)


async def create_tables():
    async with async_engine.begin() as conn:
        # Create all tables defined by the SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)


# Run the asynchronous function to create the tables
if __name__ == "__main__":
    import uvicorn
    import asyncio

    asyncio.run(create_tables())
    uvicorn.run("main:app", port=8080, host="0.0.0.0", reload=True)
