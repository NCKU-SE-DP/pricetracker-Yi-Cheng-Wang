# Python standard library
import requests

# Third-party libraries
from fastapi import APIRouter, Query

# Local imports
from src.routers.config import NECESSITIES_PRICE_API_URL

router = APIRouter()

@router.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        NECESSITIES_PRICE_API_URL,
        params={"CategoryName": category, "Name": commodity},
    ).json()