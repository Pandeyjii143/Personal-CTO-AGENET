import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
import app.models.user  # noqa: F401 — register the model with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url():
    """Use the application setting when available, otherwise alembic.ini."""
    url = getattr(settings, "database_url", None) or getattr(
        settings, "DATABASE_URL", None
    )
    return str(url) if url else config.get_main_option("sqlalchemy.url")


database_url = _database_url()
if database_url:
    # Percent signs must be escaped when values are passed to ConfigParser.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations without creating an Engine or DBAPI connection."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_sync_migrations():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            do_run_migrations(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    if "+async" in database_url:
        asyncio.run(run_async_migrations())
    else:
        run_sync_migrations()
