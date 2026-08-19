import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.apps import apps_router
from src.core.config import settings

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    logger.info("Сервис запускается...")
    yield
    logger.info("Сервис остановлен.")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)

app.include_router(router=apps_router)


@app.get("/")
async def root():
    return {"message": f"Cервис {settings.app_name} работает!"}


def start():
    import uvicorn

    uvicorn.run(
        app="main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    start()
