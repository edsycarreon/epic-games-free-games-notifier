"""Tests for Epic Games API client."""

import pytest
from unittest.mock import Mock, patch

from src.api_client import EpicGamesClient
from src.exceptions import NetworkError, InvalidResponseError


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
