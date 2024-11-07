# Third-party libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Local imports
from src.config import DATABASE_URL
from src.models import Base

database_engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(database_engine)

DatabaseSession = sessionmaker(bind=database_engine)
