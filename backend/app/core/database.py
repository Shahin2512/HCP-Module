from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Construct the database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection immediately
    with engine.connect() as connection:
        print("DEBUG: database.py - Successfully connected to the database engine.")
except Exception as e:
    print(f"ERROR: database.py - Failed to create database engine or connect: {e}")
    raise e # <--- ADD THIS LINE

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()