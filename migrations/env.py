from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context

# The development checkout keeps the application below ``Code/`` while the
# production image copies that directory's contents directly to ``/app``.
# Make the migration runner independent from that packaging detail.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for app_root in (PROJECT_ROOT / "Code", PROJECT_ROOT):
    if (app_root / "app").is_dir():
        sys.path.insert(0, str(app_root))
        break

from app.database import Base, DATABASE_URL
from app import models  # noqa: F401 - register all model metadata

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connectable = create_engine(DATABASE_URL, pool_pre_ping=True)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
