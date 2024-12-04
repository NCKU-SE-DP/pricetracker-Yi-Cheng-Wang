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
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.openai_client import LLMClient

udn_crawler = UDNCrawler()

def add_news_to_database(news_data):
    """
    Add news to database
    :param news_data: news information
    :return:
    """
    db_session = DatabaseSession()
    udn_crawler.save(news_data, db_session)

def fetch_and_process_news(is_initial=False):
    """
    get new info from news

    :param is_initial:
    :return:
    """
    SEARCH_KEYWORD = "價格"
    news_data = get_new_info(SEARCH_KEYWORD, is_initial=is_initial)
    llm_client = LLMClient(_api_key="xxx")
    for news_item in news_data:
        news_title = news_item["title"]
        relevance_check_response = llm_client.evaluate_relevance(news_title)
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

            summary_completion = llm_client.generate_summary(" ".join(news_details["content"]))
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
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        return udn_crawler.get_headline(search_term, 10)
    else:
        return udn_crawler.get_headline(search_term, 1)

def news_exists(news_id, database: Session):
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None