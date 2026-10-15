import requests
from bs4 import BeautifulSoup
import logging
from langchain_core.tools import tool

from src.config import (
    MAX_CHARACTERS,
    TIMEOUT
)


logger = logging.getLogger(__name__)


@tool
def fetch_page(
        url: str,
        max_characters: int = MAX_CHARACTERS
) -> str:
    """Fetch a webpage and return its cleaned content"""

    if max_characters <= 0:
        logger.error("max_characters must be positive and more than zero")
        raise ValueError("max_characters must be positive and more than zero")

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

    except requests.exceptions.RequestException:
        logger.exception("Error occurred while fetching webpage: %s", url)
        raise

    soup = BeautifulSoup(response.text, "html.parser")

    for s in soup(["scripts", "style", "nav", "footer", "header"]):
        s.decompose()

    text = soup.get_text(separator=" ", strip=True)

    text = " ".join(text.split())

    return text[:MAX_CHARACTERS]