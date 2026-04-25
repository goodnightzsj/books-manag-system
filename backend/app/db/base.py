from sqlalchemy import Enum as _SAEnum
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def PgEnum(python_enum, **kwargs):
    """Wrap SQLAlchemy `Enum` so the column serializes the lowercase
    `.value` ("admin") instead of the Python `.name` ("ADMIN") into the
    Postgres native enum. The migrations create the PG enums with the
    lowercase value tokens, so without this the round-trip blows up at
    INSERT time.
    """
    return _SAEnum(
        python_enum,
        values_callable=lambda cls: [e.value for e in cls],
        **kwargs,
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
