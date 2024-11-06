# Python standard library
import json
from urllib.parse import quote

# Third-party libraries
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from sqlalchemy.orm import Session

# Local imports
from src.models import NewsArticle
from src.database import DatabaseSession

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

def news_exists(news_id, database: Session):
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None