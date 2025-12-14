"""Discord notification handler (for future implementation)."""

import logging
from typing import Optional

import requests

from .config import DiscordConfig
from .models import FreeGame

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handle Discord webhook notifications."""

    def __init__(self, config: DiscordConfig) -> None:
        """
        Initialize Discord notifier.

        Args:
            config: Discord configuration
        """
        self.config = config
        self.webhook_url = config.webhook_url
        self.mention_role_id = config.mention_role_id

    def send_free_game_notification(
        self, game: FreeGame, include_image: bool = True
    ) -> bool:
        """
        Send notification about a free game to Discord.

        Args:
            game: Free game to notify about
            include_image: Whether to include game thumbnail

        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.config.enabled or not self.webhook_url:
            logger.warning("Discord notifications not enabled or webhook URL not set")
            return False

        embed = self._create_game_embed(game, include_image)
        payload = {"embeds": [embed]}

        if self.mention_role_id:
            payload["content"] = f"<@&{self.mention_role_id}>"

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Sent Discord notification for game: {game.title}")
            return True
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to send Discord notification: {exc}")
            return False

    def send_multiple_games_notification(
        self, games: list[FreeGame], title: str, include_images: bool = True
    ) -> bool:
        """
        Send notification about multiple games to Discord.

        Args:
            games: List of free games
            title: Notification title
            include_images: Whether to include game thumbnails

        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.config.enabled or not self.webhook_url:
            logger.warning("Discord notifications not enabled or webhook URL not set")
            return False

        embeds = [self._create_game_embed(game, include_images) for game in games[:10]]

        payload = {"content": f"**{title}**", "embeds": embeds}

        if self.mention_role_id:
            payload["content"] = f"<@&{self.mention_role_id}> {payload['content']}"

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Sent Discord notification for {len(games)} games")
            return True
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to send Discord notification: {exc}")
            return False

    def _create_game_embed(self, game: FreeGame, include_image: bool = True) -> dict:
        """
        Create Discord embed for a game.

        Args:
            game: Free game
            include_image: Whether to include thumbnail

        Returns:
            Discord embed dictionary
        """
        embed = {
            "title": game.title,
            "description": game.description[:500]
            + ("..." if len(game.description) > 500 else ""),
            "url": game.store_url,
            "color": 3447003,  # Blue color
            "fields": [
                {"name": "Publisher", "value": game.publisher, "inline": True},
                {"name": "Status", "value": game.status.value.title(), "inline": True},
            ],
        }

        if game.available_from:
            embed["fields"].append(
                {
                    "name": "Available From",
                    "value": game.available_from.strftime("%Y-%m-%d %H:%M UTC"),
                    "inline": True,
                }
            )

        if game.available_until:
            embed["fields"].append(
                {
                    "name": "Available Until",
                    "value": game.available_until.strftime("%Y-%m-%d %H:%M UTC"),
                    "inline": True,
                }
            )

        if include_image and game.thumbnail_url:
            embed["thumbnail"] = {"url": game.thumbnail_url}

        embed["footer"] = {"text": "Epic Games Store"}
        embed["timestamp"] = (
            game.available_from.isoformat() if game.available_from else None
        )

        return embed
