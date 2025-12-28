"""Epic Games Store API client."""

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import InvalidResponseError, NetworkError, RateLimitError
from .models import FreeGame, FreeGamesResponse

logger = logging.getLogger(__name__)


class EpicGamesClient:
    """Client for Epic Games Store API."""

    BASE_URL = "https://store-site-backend-static-ipv4.ak.epicgames.com"
    FREE_GAMES_ENDPOINT = "/freeGamesPromotions"
    TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(
        self,
        locale: str = "en-US",
        country: str = "US",
        allow_countries: Optional[str] = None,
    ) -> None:
        self.locale = locale
        self.country = country
        self.allow_countries = allow_countries or country
        self.session = self._create_session()
        logger.info(f"Initialized EpicGamesClient with locale={locale}, country={country}")

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        # Retry on rate limits (429) and server errors (5xx)
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        })

        return session

    def get_free_games(self) -> list[FreeGame]:
        url = f"{self.BASE_URL}{self.FREE_GAMES_ENDPOINT}"
        params = {
            "locale": self.locale,
            "country": self.country,
            "allowCountries": self.allow_countries,
        }

        logger.debug(f"Fetching free games from {url} with params: {params}")

        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            logger.error(f"Request timeout: {exc}")
            raise NetworkError(f"Request timeout after {self.TIMEOUT}s") from exc
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise RateLimitError("API rate limit exceeded") from exc
            logger.error(f"HTTP error: {exc}")
            raise NetworkError(f"HTTP error: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"Network error: {exc}")
            raise NetworkError(f"Network request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.error(f"Failed to parse JSON response: {exc}")
            raise InvalidResponseError("Invalid JSON response") from exc

        data = self._clean_response_errors(data)

        try:
            free_games_response = FreeGamesResponse(data=data)
            games = free_games_response.games
        except Exception as exc:
            logger.error(f"Failed to parse games from response: {exc}")
            raise InvalidResponseError(f"Failed to parse response: {exc}") from exc

        logger.info(f"Successfully fetched {len(games)} free games")
        return games

    def _clean_response_errors(self, data: dict) -> dict:
        """Epic's API returns error 1004 for region-restricted games - safe to ignore."""
        if "errors" in data:
            cleaned_errors = [
                error
                for error in data.get("errors", [])
                if error.get("errorCode") != "1004"
            ]
            if cleaned_errors:
                data["errors"] = cleaned_errors
            else:
                data.pop("errors", None)

        return data

    def get_active_games(self) -> list[FreeGame]:
        return [g for g in self.get_free_games() if g.status.value == "active"]

    def get_upcoming_games(self) -> list[FreeGame]:
        return [g for g in self.get_free_games() if g.status.value == "upcoming"]

    def close(self) -> None:
        self.session.close()
        logger.debug("Session closed")

    def __enter__(self) -> "EpicGamesClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
