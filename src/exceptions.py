"""Custom exceptions for Epic Games API client."""


class EpicGamesAPIError(Exception):
    """Base exception for Epic Games API errors."""

    pass


class NetworkError(EpicGamesAPIError):
    """Raised when network request fails."""

    pass


class InvalidResponseError(EpicGamesAPIError):
    """Raised when API response is invalid or cannot be parsed."""

    pass


class RateLimitError(EpicGamesAPIError):
    """Raised when API rate limit is exceeded."""

    pass
