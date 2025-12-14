"""Tests for Epic Games API client."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.api_client import EpicGamesClient
from src.exceptions import NetworkError, InvalidResponseError
from src.models import FreeGamesResponse, GameStatus


class TestEpicGamesClient:
    """Test suite for EpicGamesClient."""

    def test_init(self):
        """Test client initialization."""
        client = EpicGamesClient(locale="en-US", country="US")
        assert client.locale == "en-US"
        assert client.country == "US"
        assert client.allow_countries == "US"

    def test_context_manager(self):
        """Test context manager functionality."""
        with EpicGamesClient() as client:
            assert client.session is not None
        # Session should be closed after context exit

    @patch("src.api_client.requests.Session")
    def test_get_free_games_timeout(self, mock_session):
        """Test timeout handling."""
        import requests

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.side_effect = requests.exceptions.Timeout()

        client = EpicGamesClient()
        client.session = mock_session_instance

        with pytest.raises(NetworkError):
            client.get_free_games()

    @patch("src.api_client.requests.Session")
    def test_get_free_games_invalid_json(self, mock_session):
        """Test invalid JSON response handling."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session_instance.get.return_value = mock_response

        client = EpicGamesClient()
        client.session = mock_session_instance

        with pytest.raises(InvalidResponseError):
            client.get_free_games()

    def test_parse_nested_promotional_offers(self):
        """Test parsing the new nested promotional offers structure from Epic API."""
        # Mock response with the new nested structure
        mock_data = {
            "data": {
                "Catalog": {
                    "searchStore": {
                        "elements": [
                            {
                                "title": "Test Free Game",
                                "id": "test123",
                                "namespace": "namespace123",
                                "description": "A test game that is free",
                                "effectiveDate": "2025-01-01T00:00:00.000Z",
                                "seller": {"name": "Test Publisher"},
                                "keyImages": [
                                    {"type": "Thumbnail", "url": "https://example.com/image.jpg"}
                                ],
                                "promotions": {
                                    "promotionalOffers": [
                                        {
                                            "promotionalOffers": [
                                                {
                                                    "startDate": "2025-01-01T00:00:00.000Z",
                                                    "endDate": "2025-12-31T23:59:59.999Z",
                                                    "discountSetting": {
                                                        "discountType": "PERCENTAGE",
                                                        "discountPercentage": 0
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                    "upcomingPromotionalOffers": []
                                }
                            },
                            {
                                "title": "Test Discounted Game",
                                "id": "test456",
                                "namespace": "namespace456",
                                "description": "A test game with 50% discount",
                                "effectiveDate": "2025-01-01T00:00:00.000Z",
                                "seller": {"name": "Test Publisher"},
                                "keyImages": [
                                    {"type": "Thumbnail", "url": "https://example.com/image2.jpg"}
                                ],
                                "promotions": {
                                    "promotionalOffers": [
                                        {
                                            "promotionalOffers": [
                                                {
                                                    "startDate": "2025-01-01T00:00:00.000Z",
                                                    "endDate": "2025-12-31T23:59:59.999Z",
                                                    "discountSetting": {
                                                        "discountType": "PERCENTAGE",
                                                        "discountPercentage": 50
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                    "upcomingPromotionalOffers": []
                                }
                            }
                        ]
                    }
                }
            }
        }

        response = FreeGamesResponse(data=mock_data)
        games = response.games

        # Should only get the free game (0% discount), not the 50% discounted one
        assert len(games) == 1
        assert games[0].title == "Test Free Game"
        assert games[0].status == GameStatus.ACTIVE
        assert games[0].is_free is True

    def test_parse_upcoming_free_game(self):
        """Test parsing upcoming free games."""
        mock_data = {
            "data": {
                "Catalog": {
                    "searchStore": {
                        "elements": [
                            {
                                "title": "Upcoming Free Game",
                                "id": "upcoming123",
                                "namespace": "namespace789",
                                "description": "A game that will be free soon",
                                "effectiveDate": "2025-01-01T00:00:00.000Z",
                                "seller": {"name": "Test Publisher"},
                                "keyImages": [
                                    {"type": "Thumbnail", "url": "https://example.com/upcoming.jpg"}
                                ],
                                "promotions": {
                                    "promotionalOffers": [],
                                    "upcomingPromotionalOffers": [
                                        {
                                            "promotionalOffers": [
                                                {
                                                    "startDate": "2099-01-01T00:00:00.000Z",
                                                    "endDate": "2099-12-31T23:59:59.999Z",
                                                    "discountSetting": {
                                                        "discountType": "PERCENTAGE",
                                                        "discountPercentage": 0
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }

        response = FreeGamesResponse(data=mock_data)
        games = response.games

        assert len(games) == 1
        assert games[0].title == "Upcoming Free Game"
        assert games[0].status == GameStatus.UPCOMING
        assert games[0].is_free is True

    def test_handle_non_http_image_urls(self):
        """Test that non-HTTP image URLs (like video URLs) don't break parsing."""
        mock_data = {
            "data": {
                "Catalog": {
                    "searchStore": {
                        "elements": [
                            {
                                "title": "Game With Video URL",
                                "id": "video123",
                                "namespace": "namespace999",
                                "description": "A game with video URLs in keyImages",
                                "effectiveDate": "2025-01-01T00:00:00.000Z",
                                "seller": {"name": "Test Publisher"},
                                "keyImages": [
                                    {"type": "Thumbnail", "url": "https://example.com/thumb.jpg"},
                                    {"type": "Video", "url": "com.epicgames.video://test-video.mp4"}
                                ],
                                "promotions": {
                                    "promotionalOffers": [
                                        {
                                            "promotionalOffers": [
                                                {
                                                    "startDate": "2025-01-01T00:00:00.000Z",
                                                    "endDate": "2025-12-31T23:59:59.999Z",
                                                    "discountSetting": {
                                                        "discountType": "PERCENTAGE",
                                                        "discountPercentage": 0
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                    "upcomingPromotionalOffers": []
                                }
                            }
                        ]
                    }
                }
            }
        }

        response = FreeGamesResponse(data=mock_data)
        games = response.games

        # Should parse successfully despite non-HTTP URLs
        assert len(games) == 1
        assert games[0].title == "Game With Video URL"
        assert len(games[0].key_images) == 2
