from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import app.config as config
from app.database.base import Base

# ---------------------------------------------------------
# Compose connection URLs
# ---------------------------------------------------------
SERVER_URL = (
    f"mysql+pymysql://{config.DB_USERNAME}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{config.DB_PORT}"
)

DATABASE_URL = f"{SERVER_URL}/{config.DB_DATABASE}"

# ---------------------------------------------------------
# Create database if missing
# ---------------------------------------------------------
def create_database_if_missing():
    """
    Connects to MySQL server (no DB), checks if target DB exists,
    creates it if missing.
    """
    temp_engine = create_engine(SERVER_URL)

    with temp_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db"
            ),
            {"db": config.DB_DATABASE}
        )
        if not result.fetchone():
            connection.execute(text(f"CREATE DATABASE `{config.DB_DATABASE}`"))
            connection.commit()
            print(f"✅ Database '{config.DB_DATABASE}' created successfully.")
        else:
            print(f"✅ Database '{config.DB_DATABASE}' already exists.")

create_database_if_missing()

# ---------------------------------------------------------
# Main engine and session
# ---------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------
# Create tables
# ---------------------------------------------------------
from app.models.database import chat

def create_all_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Checked/created all tables (chat table only).")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

create_all_tables()

# ---------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()