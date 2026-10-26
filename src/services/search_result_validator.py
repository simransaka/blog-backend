import requests
import logging
from typing import List

from src.state import State
from src.models import EvidenceItem


logger = logging.getLogger(__name__)


def search_result_validator(evidence: EvidenceItem) -> EvidenceItem | None:
    """Validate one search result URL."""
    logger.info("Validation of evidence (url) started...")
    try:
        response = requests.get(
            evidence.url,
            timeout=10,
            allow_redirects=True
        )
            
        if response.status_code == 200:
            logger.info("Evidence (url) is valid")
            return evidence
        else:
            logger.warning(
                f"""Removing inaccessible evidence: 
                {evidence.url} with status code {response.status_code}""")
    except requests.RequestException as e:
        logger.warning(
            f"""Falied to access evidence for {evidence.url}
            with an exception {e}"""
        )

    return None