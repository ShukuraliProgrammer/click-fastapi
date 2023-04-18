from pydantic import BaseSettings
from dotenv import load_dotenv
from os import environ
load_dotenv()

print("environ.get('CLICK_SERVICE_ID'), ", environ.get('CLICK_SERVICE_ID'))

class Settings(BaseSettings):
    APP_NAME: str = "Click API"
    APP_VERSION: str = "0.0.1"

    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str
    print("environ.get('CLICK_SERVICE_ID'), ", environ.get('CLICK_SERVICE_ID'))
    CLICK_SETTINGS = {
        'service_id': environ.get('CLICK_SERVICE_ID'),
        'merchant_id': environ.get('CLICK_MERCHANT_ID'),
        'secret_key': environ.get('CLICK_SECRET_KEY'),
        'merchant_user_id': environ.get('CLICK_MERCHANT_USER_ID'),
    }

    class Config:
        env_file = './.env'


settings = Settings()
