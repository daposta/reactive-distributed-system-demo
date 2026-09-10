from sqlalchemy import create_engine, QueuePool
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.settings import settings

engine = create_engine(settings.DATABASE_URL, poolclass=QueuePool, pool_size=5, max_overflow=10)
Base = declarative_base()

Session = sessionmaker(bind=engine)


def get_session():
    with Session() as session:
        yield session
