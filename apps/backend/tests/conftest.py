import os

os.environ.setdefault("APP_ENV", "test")
os.environ["APP_SECRET_KEY"] = "test-secret-key-0123456789abcdef0123"
os.environ["TELEGRAM_BOT_API_KEY"] = "test-bot-key-0123456789abcdef"
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import UTC, datetime  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import MonitoringSource, User  # noqa: E402
from app.models.enums import SourceType  # noqa: E402
from app.services.rate_limit import login_limiter  # noqa: E402

PASSWORD = "Sinov-parol-12345"
BOT = {"X-Bot-Api-Key": "test-bot-key-0123456789abcdef"}


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(eng, "connect")
    def _fk(dbapi_conn, _):  # noqa: ANN001
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture()
def app(engine):
    application = create_app()
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def _get_db():
        with factory() as s:
            yield s

    application.dependency_overrides[get_db] = _get_db
    return application


@pytest.fixture(autouse=True)
def _reset_limiter():
    login_limiter.reset()


@pytest.fixture()
def user(db):
    u = User(username="ali", email="ali@example.uz", password_hash=hash_password(PASSWORD))
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def auth(client, user):
    """Login qilingan klient; CSRF sarlavhasi avtomatik qo'shiladi."""
    r = client.post("/api/v1/auth/login", json={"identifier": "ali", "password": PASSWORD})
    assert r.status_code == 200
    client.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    return client


@pytest.fixture()
def source(db):
    s = MonitoringSource(name="Test kanal", telegram_chat_id=-1001, source_type=SourceType.CHANNEL)
    db.add(s)
    db.commit()
    return s


def make_message(message_id: int, text: str, chat_id: int = -1001, **extra):
    return {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "timestamp": datetime.now(UTC).isoformat(),
        **extra,
    }


def add_rule(client, keyword="quvur yorildi", **extra):
    body = {"name": keyword, "keyword": keyword, "category": "PIPE_BURST", "priority": 80, **extra}
    r = client.post("/api/v1/detection-rules", json=body)
    assert r.status_code == 201, r.text
    return r.json()
