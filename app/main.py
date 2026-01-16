from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import DECLARATIVE_BASE, postgresql_engine
from contextlib import asynccontextmanager
from routers.health import health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with postgresql_engine.begin() as connection:
        await connection.run_sync(DECLARATIVE_BASE.metadata.create_all)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

#Routers
app.include_router(health_router)
