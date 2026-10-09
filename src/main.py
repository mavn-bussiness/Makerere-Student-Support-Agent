from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Makerere Student Support Agent"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


from src.api.llm import router as llm_router
from src.api.rag import router as rag_router
from src.api.tools import router as tools_router
from src.api.memory import router as memory_router
from src.api.hitl import router as hitl_router

settings = Settings()
app = FastAPI(title=settings.app_name)

app.include_router(llm_router, prefix="/api/v1/llm")
app.include_router(rag_router, prefix="/api/v1/rag")
app.include_router(tools_router, prefix="/api/v1/tools")
app.include_router(memory_router, prefix="/api/v1/memory")
app.include_router(hitl_router, prefix="/api/v1/hitl")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"name": settings.app_name, "environment": settings.environment}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

