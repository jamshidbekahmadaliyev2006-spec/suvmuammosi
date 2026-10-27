from pathlib import Path
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine = None
_factory: sessionmaker[Session] | None = None


def get_engine():  # type: ignore[no-untyped-def]
    global _engine, _factory
    if _engine is None:
        url = get_settings().database_url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False, "timeout": 60}
            if "///." in url or url == "sqlite:///suvnazorat.db":
                backend_dir = Path(__file__).resolve().parent.parent.parent
                db_path = backend_dir / "suvnazorat.db"
                url = f"sqlite:///{db_path.as_posix()}"
        _engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        if url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _):  # type: ignore[no-untyped-def]
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=60000")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        _factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_db() -> Iterator[Session]:
    get_engine()
    assert _factory is not None
    with _factory() as session:
        yield session


def session_scope() -> Session:
    """CLI skriptlari uchun (with bilan ishlatiladi)."""
    get_engine()
    assert _factory is not None
    return _factory()
