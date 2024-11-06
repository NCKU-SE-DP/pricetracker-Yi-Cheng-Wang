# Third-party libraries
from sqlalchemy.orm import sessionmaker

# Local imports
from src.database import DatabaseSession, database_engine

def session_opener():
    db_session = DatabaseSession(bind=database_engine)
    try:
        yield db_session
    finally:
        db_session.close()