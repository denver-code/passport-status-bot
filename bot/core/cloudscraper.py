import asyncio

import cloudscraper
import requests
from cloudscraper import CloudScraper

from bot.core.logger import log_error, log_function, log_info


@log_function("cloudscraper_init")
async def cloudscraper_init(proxy_urls: list[str], debug: bool = False) -> CloudScraper:
    """Create and return a CloudScraper instance."""

    def _create_scraper() -> CloudScraper:
        scraper: CloudScraper = cloudscraper.create_scraper(
            interpreter="js2py",
            browser={"browser": "chrome", "platform": "windows", "mobile": False},
            debug=debug,
        )
        return scraper

    return await asyncio.to_thread(_create_scraper)


@log_function("cloudscraper_get")
async def cloudscraper_get(
    scraper: CloudScraper, test_url: str
) -> requests.Response | None:
    """Fetch a URL using CloudScraper."""
    try:

        def _get() -> requests.Response:
            response: requests.Response = scraper.get(test_url, timeout=30)
            return response

        response = await asyncio.to_thread(_get)
        log_info(f"Cloudscraper {test_url} response: {response.status_code}")
        return response

    except Exception as e:
        log_error(f"Error in cloudscraper_get: {e}")
        return None
