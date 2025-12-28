"""Epic Games API exceptions."""


class EpicGamesAPIError(Exception):
    pass


class NetworkError(EpicGamesAPIError):
    pass


class InvalidResponseError(EpicGamesAPIError):
    pass


class RateLimitError(EpicGamesAPIError):
    pass
