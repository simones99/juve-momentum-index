import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db import Base, get_db
from app.main import app

settings = get_settings()
_base_url = make_url(settings.database_url)
_test_db_name = f"{_base_url.database}_test"

# In CI, TEST_DATABASE_URL should point directly at the ephemeral Postgres
# service container's own database (nothing to protect there). Locally, we
# default to a separate "<db>_test" database so running pytest never touches
# -- and never DROPs -- your dev database.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or str(_base_url.set(database=_test_db_name))


def _ensure_test_database_exists() -> None:
    admin_engine = create_engine(_base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _test_db_name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{_test_db_name}"'))
    finally:
        admin_engine.dispose()


if "TEST_DATABASE_URL" not in os.environ:
    _ensure_test_database_exists()

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db(_schema):
    """A session bound to a connection wrapped in a transaction that's
    rolled back after each test, for isolation without recreating tables."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
