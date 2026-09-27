from contextlib import contextmanager

from sqlalchemy import create_engine, QueuePool
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.settings import settings

engine = create_engine(settings.DATABASE_URL, poolclass=QueuePool, pool_size=5, max_overflow=10)
Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session


@contextmanager
def get_db_session():
    with SessionLocal() as session:
        yield session
