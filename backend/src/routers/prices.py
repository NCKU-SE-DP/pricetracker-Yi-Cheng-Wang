# Python standard library
import requests
import logging
from sentry_sdk import capture_exception

# Third-party libraries
from fastapi import APIRouter, Query

# Local imports
from src.routers.config import NECESSITIES_PRICE_API_URL

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    try:
        return requests.get(
            NECESSITIES_PRICE_API_URL,
            params={"CategoryName": category, "Name": commodity},
        ).json()
    except Exception as e:
        logger.error("Error fetching necessities prices: %s", e)
        capture_exception(e)
        return {"error": "An error occurred while fetching prices."}