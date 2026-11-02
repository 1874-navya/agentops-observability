import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentops.api.main import app
from agentops.core.config import get_settings
from agentops.storage.database import Base, get_session


@pytest.fixture()
def client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=test_engine, expire_on_commit=False)
    Base.metadata.create_all(test_engine)

    def override_session():
        with testing_session() as session:
            yield session

    monkeypatch.setenv("AGENTOPS_API_KEY", "test-key")
    get_settings.cache_clear()
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()
