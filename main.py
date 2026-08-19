from fastapi import FastAPI
from src.core.config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Сервис запускается...")
    yield
    print("Сервис остановлен.")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)


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
