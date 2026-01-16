from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from loguru import logger



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
