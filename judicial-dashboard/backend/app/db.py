import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        return db_url
    # Fallback to SQLite for local development
    return "sqlite:///./judicial.db"


DATABASE_URL = get_database_url()

# For SQLite need check_same_thread
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


