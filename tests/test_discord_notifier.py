"""Tests for Discord notifier."""

import pytest
from datetime import datetime, timezone

from src.discord_notifier import DiscordNotifier, PHT
from src.config import DiscordConfig
from src.models import FreeGame, GameStatus


class TestDiscordNotifier:
    """Test suite for DiscordNotifier."""

    def test_format_datetime_pht(self):
        """Test PHT datetime formatting."""
        config = DiscordConfig(enabled=False)
        notifier = DiscordNotifier(config)

        # Test UTC to PHT conversion (UTC+8)
        utc_time = datetime(2025, 12, 18, 16, 0, 0, tzinfo=timezone.utc)
        formatted = notifier._format_datetime_pht(utc_time)

        # 16:00 UTC = 00:00 next day PHT
        assert formatted == "2025-12-19 00:00 PHT"

    def test_embed_with_placeholder_description(self):
        """Test that placeholder descriptions (title == description) are handled."""
        config = DiscordConfig(enabled=False)
        notifier = DiscordNotifier(config)

        # Create a mock game with title as description (Epic's API limitation)
        game = FreeGame(
            title="Hogwarts Legacy",
            description="Hogwarts Legacy",
            id="test123",
            namespace="test",
            seller={"name": "Epic Dev Test Account"},
            effectiveDate="2025-01-01T00:00:00.000Z",
            keyImages=[],
            promotions={
                "promotionalOffers": [
                    {
                        "promotionalOffers": [
                            {
                                "startDate": "2025-12-12T02:23:00.000Z",
                                "endDate": "2025-12-18T16:00:00.000Z",
                                "discountSetting": {
                                    "discountType": "PERCENTAGE",
                                    "discountPercentage": 0,
                                },
                            }
                        ]
                    }
                ],
                "upcomingPromotionalOffers": [],
            },
        )

        embed = notifier._create_game_embed(game, include_image=True)

        # Description should be replaced with a helpful message, not just the title
        assert embed["description"] != "Hogwarts Legacy"
        assert "Free game available" in embed["description"]
        assert "Epic Games Store" in embed["description"]

    def test_embed_with_proper_description(self):
        """Test that proper descriptions are preserved."""
        config = DiscordConfig(enabled=False)
        notifier = DiscordNotifier(config)

        # Create a mock game with a real description
        proper_description = "Ghostrunner 2 is a hardcore FPP slasher set in a post-apocalyptic, cyberpunk world."
        game = FreeGame(
            title="Ghostrunner 2",
            description=proper_description,
            id="test456",
            namespace="test",
            seller={"name": "505 Games"},
            effectiveDate="2025-01-01T00:00:00.000Z",
            keyImages=[],
            promotions={
                "promotionalOffers": [
                    {
                        "promotionalOffers": [
                            {
                                "startDate": "2025-12-11T16:00:00.000Z",
                                "endDate": "2026-01-08T16:00:00.000Z",
                                "discountSetting": {
                                    "discountType": "PERCENTAGE",
                                    "discountPercentage": 20,
                                },
                            }
                        ]
                    }
                ],
                "upcomingPromotionalOffers": [],
            },
        )

        embed = notifier._create_game_embed(game, include_image=True)

        # Proper description should be preserved
        assert embed["description"] == proper_description

    def test_embed_pht_timestamps(self):
        """Test that embed fields show PHT timestamps."""
        config = DiscordConfig(enabled=False)
        notifier = DiscordNotifier(config)

        game = FreeGame(
            title="Test Game",
            description="Test description for a game",
            id="test789",
            namespace="test",
            seller={"name": "Test Publisher"},
            effectiveDate="2025-01-01T00:00:00.000Z",
            keyImages=[],
            promotions={
                "promotionalOffers": [
                    {
                        "promotionalOffers": [
                            {
                                "startDate": "2025-12-18T16:00:00.000Z",
                                "endDate": "2025-12-19T16:00:00.000Z",
                                "discountSetting": {
                                    "discountType": "PERCENTAGE",
                                    "discountPercentage": 0,
                                },
                            }
                        ]
                    }
                ],
                "upcomingPromotionalOffers": [],
            },
        )

        embed = notifier._create_game_embed(game, include_image=True)

        # Find the timestamp fields
        timestamp_fields = [f for f in embed["fields"] if "Available" in f["name"]]

        # All timestamp fields should end with "PHT"
        for field in timestamp_fields:
            assert field["value"].endswith("PHT")
