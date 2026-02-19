from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    AI_PROVIDER: str = "gemini"
    INPUT_DIR: str = "data/fanga_inbox"
    OUTPUT_DIR: str = "data/fanga_organised"
    CONFIDENCE_THRESHOLD: float = 0.7
    MODEL_NAME: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"



settings = Settings()
