from app.core.database import get_db

def get_db_session():
    yield from get_db()