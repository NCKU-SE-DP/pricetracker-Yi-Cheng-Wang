import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

USER_NEWS_ASSOCIATION_TABLE_NAME = "user_news_upvotes"
USERS_TABLE_NAME = "users"
NEWS_ARTICLES_TABLE_NAME = "news_articles"

user_news_association_table = Table(
    USER_NEWS_ASSOCIATION_TABLE_NAME,
    Base.metadata,
    Column("user_id", Integer, ForeignKey(f"{USERS_TABLE_NAME}.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey(f"{NEWS_ARTICLES_TABLE_NAME}.id"), primary_key=True
    ),
)

# from pydantic import BaseModel

MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_HASH_LENGTH = 200

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


DATABASE_URL = "sqlite:///news_database.db"
database_engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(database_engine)

DatabaseSession = sessionmaker(bind=database_engine)

SENTRY_DSN = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"
SENTRY_TRACES_SAMPLE_RATE = 1.0
SENTRY_PROFILES_SAMPLE_RATE = 1.0

sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database_engine)

ALLOWED_ORIGIN = "http://localhost:8080"

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from openai import OpenAI


# def generate_summary(content):
#     messages = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=messages,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     messages = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=messages,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def add_news_to_database(news_data):
    """
    Add news to database
    :param news_data: news information
    :return:
    """
    db_session = DatabaseSession()
    db_session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # Convert content list to string
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    db_session.commit()
    db_session.close()


def get_new_info(search_term, is_initial=False):
    """
    get news data

    :param search_term:
    :param is_initial:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        news_pages = []
        MAX_PAGES = 10
        for page in range(1, MAX_PAGES):
            params = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=params)
            news_pages.append(response.json()["lists"])

        for news_list in news_pages:
            all_news_data.append(news_list)
    else:
        params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=params)

        all_news_data = response.json()["lists"]
    return all_news_data

def fetch_and_process_news(is_initial=False):
    """
    get new info from news

    :param is_initial:
    :return:
    """
    SEARCH_KEYWORD = "價格"
    news_data = get_new_info(SEARCH_KEYWORD, is_initial=is_initial)
    for news_item in news_data:
        news_title = news_item["title"]
        relevance_check_messages = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{news_title}"},
        ]
        relevance_check_response = OpenAI(api_key="xxx").chat.completions.create(
            model="gpt-3.5-turbo",
            messages=relevance_check_messages,
        )
        relevance_level = relevance_check_response.choices[0].message.content
        if relevance_level == "high":
            response = requests.get(news_item["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # Title
            article_title = soup.find("h1", class_="article-content__title").text
            article_time = soup.find("time", class_="article-content__time").text
            # Locate the <section> containing article content
            content_section = soup.find("section", class_="article-content__editor")

            article_paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            news_details =  {
                "url": news_item["titleLink"],
                "title": article_title,
                "time": article_time,
                "content": article_paragraphs,
            }
            summary_generation_messages = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(news_details["content"])},
            ]

            summary_completion = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=summary_generation_messages,
            )
            summary_result = json.loads(summary_completion.choices[0].message.content)
            news_details["summary"] = summary_result["影響"]
            news_details["reason"] = summary_result["原因"]
            add_news_to_database(news_details)


@app.on_event("startup")
def start_scheduler():
    database = SessionLocal()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        fetch_and_process_news()
    database.close()
    FETCH_INTERVAL_MINUTES = 100
    background_scheduler.add_job(fetch_and_process_news, "interval", minutes=FETCH_INTERVAL_MINUTES)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def session_opener():
    db_session = DatabaseSession(bind=database_engine)
    try:
        yield db_session
    finally:
        db_session.close()



def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def check_user_password_is_correct(database, username, password):
    user = database.query(User).filter(User.username == username).first()
    if not verify_password(password, user.hashed_password):
        return False
    return user

JWT_SECRET_KEY = '1892dhianiandowqd0n'

def authenticate_user_token(
    token = Depends(OAUTH2_SCHEME),
    database = Depends(session_opener)
):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return database.query(User).filter(User.username == payload.get("sub")).first()


def create_access_token(data, expires_delta=None):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        DEFAULT_TOKEN_EXPIRE_MINUTES = 15
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(session_opener)
):
    """login"""
    user = check_user_password_is_correct(database, form_data.username, form_data.password)
    TOKEN_EXPIRE_MINUTES = 30
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str
@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, database: Session = Depends(session_opener)):
    """create user"""
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    database.add(new_user)
    database.commit()
    database.refresh(new_user)
    return new_user


@app.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}


INITIAL_ID = 1000000
id_counter = itertools.count(start=INITIAL_ID)


def get_article_upvote_details(article_id, user_id, database):
    upvote_count = (
        database.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    is_upvoted = False
    if user_id:
        is_upvoted = (
                database.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
        )
    return upvote_count, is_upvoted


@app.get("/api/v1/news/news")
def read_news(database=Depends(session_opener)):
    """
    read news

    :param database:
    :return:
    """
    news_articles = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news_articles:
        upvotes, upvoted = get_article_upvote_details(article.id, None, database)
        result.append(
            {**article.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
        )
    return result


@app.get(
    "/api/v1/news/user_news"
)
def read_user_news(
        database=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """
    read user news

    :param database:
    :param user:
    :return:
    """
    news_articles = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news_articles:
        upvotes, upvoted = get_article_upvote_details(article.id, user.id, database)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return result

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    user_prompt = request.prompt
    news_list = []
    keyword_extraction_messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{user_prompt}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=keyword_extraction_messages,
    )
    extracted_keywords = completion.choices[0].message.content
    # Should change into simple factory pattern
    news_items = get_new_info(extracted_keywords, is_initial=False)
    for news_item in news_items:
        try:
            response = requests.get(news_item["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # Title
            article_title = soup.find("h1", class_="article-content__title").text
            article_time = soup.find("time", class_="article-content__time").text
            # Locate the <section> containing article content
            content_section = soup.find("section", class_="article-content__editor")

            article_paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            article_details = {
                "url": news_item["titleLink"],
                "title": article_title,
                "time": article_time,
                "content": article_paragraphs,
            }
            article_details["content"] = " ".join(article_details["content"])
            article_details["id"] = next(id_counter)
            news_list.append(article_details)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSumaryRequestSchema(BaseModel): #The class name is incorrect, but it hasn't been changed because it would affect the tests.
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    summary_response = {}
    summary_generation_messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=summary_generation_messages,
    )
    summary_result = completion.choices[0].message.content
    if summary_result:
        summary_result = json.loads(summary_result)
        summary_response["summary"] = summary_result["影響"]
        summary_response["reason"] = summary_result["原因"]
    return summary_response


@app.post("/api/v1/news/{id}/upvote")
def upvote_article(
        id,
        database=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    upvote_message = toggle_upvote(id, user.id, database)
    return {"message": upvote_message}


def toggle_upvote(news_id, user_id, database):
    existing_upvote = database.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        database.execute(delete_stmt)
        database.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        database.execute(insert_stmt)
        database.commit()
        return "Article upvoted"


def news_exists(news_id, database: Session):
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    NECESSITIES_PRICE_API_URL = "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice"
    return requests.get(
        NECESSITIES_PRICE_API_URL,
        params={"CategoryName": category, "Name": commodity},
    ).json()
