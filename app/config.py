from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Click API"
    APP_VERSION: str = "0.0.1"

    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str

    CLICK_SETTINGS = {
        'service_id': "26422",
        'merchant_id': "18648",
        'secret_key': "SIL0aI5ijxl0TbL",
        'merchant_user_id': "30092",
    }

    class Config:
        env_file = './.env'


settings = Settings()
