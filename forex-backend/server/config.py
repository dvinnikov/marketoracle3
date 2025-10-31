from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    STRATEGIES_DIR: str = "server/strategies"
    AGG_TF: list[int] = [1,5,15,60]  # minutes
    MAX_BARS: int = 2000

settings = Settings()
