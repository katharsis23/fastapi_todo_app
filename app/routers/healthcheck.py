from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from loguru import logger
from app.s3_client import s3_client
from app.redis_client import redis_session


health_router = APIRouter(prefix="/health")


@health_router.get("/healthcheck", response_class=JSONResponse, description="Healthcheck of the server")
async def healthcheck():
    try:
        return JSONResponse(
            content={
                "server_status": "OK"
            },
            status_code=status.HTTP_200_OK
        )
    except HTTPException as http_exception:
        logger.error(f"Error occured during /healthcheck: {http_exception}")


@health_router.get("/s3_healthcheck", status_code=status.HTTP_200_OK)
async def s3_healthcheck():
    try:
        async with s3_client.get_client() as client:
            await client.list_buckets()

        return {"status": "healthy", "message": "S3 server is reachable"}

    except Exception as e:
        logger.error(f"S3 Healthcheck failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "detail": str(e)}
        )


@health_router.get("/redis_healthcheck", description="Healthcheck of the Redis server")
async def redis_healthcheck():
    try:
        async with redis_session() as session:
            await session.set("healthcheck_key", "ok", ex=10)
            value = await session.get("healthcheck_key")

            if value == "ok":
                return {
                    "status": "healthy",
                    "message": "Redis server is reachable",
                }
            raise Exception("Redis returned unexpected value")

    except Exception as error:
        logger.error(f"Redis Healthcheck failed: {error}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "detail": str(error)}
        )
