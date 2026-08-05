"""Engine, WAL mode and session factory.

WAL + a short busy timeout is the README's answer to SQLite lock contention under the
demo's 1–2 concurrent users (§6, §12). A single writer per container keeps this safe.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from telecom_agent.store.models import Base

_engine: Engine | None = None
_Session: sessionmaker[Session] | None = None


def _configure_sqlite(dbapi_conn, _record) -> None:
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA busy_timeout=5000;")
    cur.close()


def init_engine(database_url: str) -> Engine:
    global _engine, _Session
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_engine(database_url, connect_args=connect_args, future=True)
    if database_url.startswith("sqlite"):
        event.listen(_engine, "connect", _configure_sqlite)
    _Session = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def create_all(database_url: str) -> None:
    engine = init_engine(database_url)
    Base.metadata.create_all(engine)


def get_sessionmaker() -> sessionmaker[Session]:
    if _Session is None:
        raise RuntimeError("engine not initialised; call init_engine()/create_all() first")
    return _Session
