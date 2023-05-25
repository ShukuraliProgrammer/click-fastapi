from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(docs_url="/", title=settings.APP_NAME, version=settings.APP_VERSION)

    register_tortoise(
        app,
        db_url=get_db_uri(
            user=settings.POSTGRES_USER,
            passwd=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOSTNAME,
            db=settings.POSTGRES_DB
        ),
        modules={"models": ["app.click.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    register_views(app=app)

    return app


def get_db_uri(user, passwd, host, db):
    return f"postgres://{user}:{passwd}@{host}:5432/{db}"


def register_views(app: FastAPI):
    from app.api.transaction import router as create_click_transaction
    from app.api.pyclick_merchant import router as click_merchant
    app.include_router(create_click_transaction, prefix="/pyclick/process/click", tags=["Click"])
    app.include_router(click_merchant, prefix="/pyclick/process/click", tags=["Click"])
