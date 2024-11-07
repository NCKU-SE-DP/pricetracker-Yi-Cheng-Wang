# Third party imports
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Local application imports
from src.config import (
    MAX_PASSWORD_HASH_LENGTH,
    MAX_USERNAME_LENGTH,
    NEWS_ARTICLES_TABLE_NAME,
    USER_NEWS_ASSOCIATION_TABLE_NAME,
    USERS_TABLE_NAME,
)

Base = declarative_base()

user_news_association_table = Table(
    USER_NEWS_ASSOCIATION_TABLE_NAME,
    Base.metadata,
    Column("user_id", Integer, ForeignKey(f"{USERS_TABLE_NAME}.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey(f"{NEWS_ARTICLES_TABLE_NAME}.id"), primary_key=True
    ),
)

class User(Base):
    __tablename__ = USERS_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(MAX_USERNAME_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(MAX_PASSWORD_HASH_LENGTH), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )

class NewsArticle(Base):
    __tablename__ = NEWS_ARTICLES_TABLE_NAME
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )
