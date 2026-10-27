from logging.config import fileConfig

from sqlalchemy import create_engine

import app.models  # noqa: F401  (jadvallarni metadata ga yuklaydi)
from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.db.types import UTCDateTime

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):  # noqa: ANN001, ANN201
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def run() -> None:
    url = get_settings().database_url
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                          render_item=render_item)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(
            connection=conn, target_metadata=target_metadata, render_item=render_item,
            render_as_batch=conn.dialect.name == "sqlite", compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


run()
