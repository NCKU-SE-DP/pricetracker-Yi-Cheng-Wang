# Python standard library
import itertools
import json

# Third-party imports
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from openai import OpenAI
import requests
from sqlalchemy.orm import Session

# Local application imports
from src.auth.services import authenticate_user_token
from src.dependencies import session_opener
from src.feature.news.services import get_new_info, udn_crawler
from src.feature.upvote.services import get_article_upvote_details, toggle_upvote
from src.models import NewsArticle
from src.routers.config import INITIAL_ID
from src.schemas import NewsSumaryRequestSchema, PromptRequest

_id_counter = itertools.count(start=INITIAL_ID)

router = APIRouter()

@router.get("/api/v1/news/news")
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

@router.get("/api/v1/news/user_news")
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

@router.post("/api/v1/news/search_news")
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
            article_details["id"] = next(_id_counter)
            news_list.append(article_details)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/api/v1/news/news_summary")
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

@router.post("/api/v1/news/{id}/upvote")
def upvote_article(
        id,
        database=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    upvote_message = toggle_upvote(id, user.id, database)
    return {"message": upvote_message}
