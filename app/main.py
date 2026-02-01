from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import DeclarativeBase, postgresql_engine
from contextlib import asynccontextmanager
from app.routers.healthcheck import health_router
from app.routers.user import user_router
from app.routers.task import tasks_router
from app.middleware.logging import LoggingMiddleware, ErrorHandlingMiddleware
from loguru import logger
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with postgresql_engine.begin() as connection:
        await connection.run_sync(DeclarativeBase.metadata.create_all)
        logger.debug(f"Tables in metadata: {DeclarativeBase.metadata.tables.keys()}")
        logger.info(f"App is running in Development mode: {os.getenv('DEVELOPMENT_MODE')}")
        yield
    await postgresql_engine.dispose()


# App core
app = FastAPI(
    title="FastApi_todo_app",
    version="0.0.1",
    summary="Simple todo app created as a pet project",
    lifespan=lifespan
)

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

# Routers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(tasks_router)
