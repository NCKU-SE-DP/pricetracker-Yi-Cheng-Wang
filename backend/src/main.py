# Third-party imports
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from sentry_sdk import capture_exception

# Local application imports
from src.config import (
    SENTRY_DSN,
    SENTRY_PROFILES_SAMPLE_RATE,
    SENTRY_TRACES_SAMPLE_RATE,
    FETCH_INTERVAL_MINUTES
)
from src.database import database_engine
from src.feature.news.services import fetch_and_process_news
from src.models import NewsArticle
from src.routers import news, prices, users
from src.utils import init_logger_no_rotation

init_logger_no_rotation()

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

app.include_router(news.router)
app.include_router(prices.router)
app.include_router(users.router)

@app.on_event("startup")
def start_scheduler():
    database = SessionLocal()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        fetch_and_process_news()
    database.close()
    background_scheduler.add_job(fetch_and_process_news, "interval", minutes=FETCH_INTERVAL_MINUTES)
    background_scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()
