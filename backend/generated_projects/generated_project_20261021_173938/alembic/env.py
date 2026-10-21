import asyncio
import logging.config

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
import app.models.user  # noqa: F401 — register models with Base.metadata

config = context.config

if config.config_file_name is not None:
    logging.config.fileConfig(config.config_file_name)


target_metadata = Base.metadata


def _database_url() -> str:
    url = getattr(settings, "database_url", None) or getattr(
        settings, "DATABASE_URL", None
    )
    if url is None:
        raise RuntimeError("A database URL must be configured in application settings")
    if hasattr(url, "get_secret_value"):
        url = url.get_secret_value()
    return str(url)


config.set_main_option("sqlalchemy.url", _database_url().replace("%", "%%"))


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _configure_connection(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _is_async_url(url: str) -> bool:
    return any(
        driver in url
        for driver in ("+asyncpg", "+aiosqlite", "+asyncmy", "+aiomysql")
    )


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _database_url()

    if _is_async_url(section["sqlalchemy.url"]):
        asyncio.run(_run_async_migrations(section))
        return

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        with connectable.connect() as connection:
            _configure_connection(connection)
    finally:
        connectable.dispose()


async def _run_async_migrations(section: dict) -> None:
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(_configure_connection)
    finally:
        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
