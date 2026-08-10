from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if not settings.mysql_password:
        raise RuntimeError("缺少 MYSQL_PASSWORD 环境变量")

    password = quote_plus(settings.mysql_password)
    url = (
        f"mysql+pymysql://{settings.mysql_user}:{password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        "?charset=utf8mb4"
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 5},
    )
