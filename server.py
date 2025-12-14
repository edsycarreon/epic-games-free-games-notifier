#!/usr/bin/env python3
"""Web server for Google Cloud Run deployment.

This server provides HTTP endpoints for Cloud Scheduler to trigger
the Epic Games free games check and send notifications.
"""

import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from src.api_client import EpicGamesClient
from src.config import load_config, setup_logging
from src.discord_notifier import DiscordNotifier
from src.exceptions import EpicGamesAPIError

# Initialize logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = load_config()
    setup_logging(config.logging)
    logger.info("Configuration loaded successfully")
except Exception as exc:
    logger.error(f"Failed to load configuration: {exc}")
    config = None


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Cloud Run health checks and scheduled tasks."""

    def log_message(self, format: str, *args) -> None:
        """Override to use Python logging instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")

    def _send_response(self, status_code: int, message: str) -> None:
        """
        Send HTTP response.

        Args:
            status_code: HTTP status code
            message: Response message
        """
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = f'{{"status": "{message}"}}\n'
        self.wfile.write(response.encode())

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health" or self.path == "/":
            self._handle_health()
        elif self.path == "/check":
            self._handle_check()
        else:
            self._send_response(404, "Not Found")

    def do_POST(self) -> None:
        """Handle POST requests (for Cloud Scheduler)."""
        if self.path == "/check":
            self._handle_check()
        else:
            self._send_response(404, "Not Found")

    def _handle_health(self) -> None:
        """Handle health check endpoint."""
        self._send_response(200, "healthy")

    def _handle_check(self) -> None:
        """Handle the main check endpoint that fetches games and sends notifications."""
        if config is None:
            logger.error("Configuration not loaded")
            self._send_response(500, "Configuration error")
            return

        try:
            logger.info("Starting Epic Games free games check")

            # Create API client and fetch games
            with EpicGamesClient(
                locale=config.epic_games.locale,
                country=config.epic_games.country,
                allow_countries=config.epic_games.allow_countries,
            ) as client:
                all_games = client.get_free_games()
                active_games = [g for g in all_games if g.status.value == "active"]
                upcoming_games = [g for g in all_games if g.status.value == "upcoming"]

                logger.info(
                    f"Found {len(active_games)} active and {len(upcoming_games)} upcoming games"
                )

                # Send Discord notifications if enabled
                if config.discord.enabled:
                    notifier = DiscordNotifier(config.discord)
                    notifications_sent = 0

                    if active_games and config.notifications.notify_current_games:
                        success = notifier.send_multiple_games_notification(
                            active_games,
                            "🎮 Free Games Available Now!",
                            config.notifications.include_game_images,
                        )
                        if success:
                            notifications_sent += 1

                    if upcoming_games and config.notifications.notify_upcoming_games:
                        success = notifier.send_multiple_games_notification(
                            upcoming_games,
                            "📅 Upcoming Free Games",
                            config.notifications.include_game_images,
                        )
                        if success:
                            notifications_sent += 1

                    logger.info(f"Sent {notifications_sent} Discord notifications")
                else:
                    logger.info("Discord notifications disabled")

                # Log game information
                for game in active_games:
                    logger.info(f"Active: {game.title} - {game.store_url}")
                for game in upcoming_games:
                    logger.info(f"Upcoming: {game.title} - {game.store_url}")

                self._send_response(
                    200,
                    f"Success: {len(active_games)} active, {len(upcoming_games)} upcoming",
                )

        except EpicGamesAPIError as exc:
            logger.error(f"API error: {exc}")
            self._send_response(500, f"API error: {exc}")
        except Exception as exc:
            logger.exception(f"Unexpected error: {exc}")
            self._send_response(500, f"Error: {exc}")


def run_server(port: int = 8080) -> None:
    """
    Run the HTTP server.

    Args:
        port: Port to listen on (default: 8080 for Cloud Run)
    """
    server_address = ("", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)

    logger.info(f"Server starting on port {port}")
    logger.info(f"Health check endpoint: http://localhost:{port}/health")
    logger.info(f"Check endpoint: http://localhost:{port}/check")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.shutdown()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    port = int(os.environ.get("PORT", 8080))

    try:
        run_server(port)
        return 0
    except Exception as exc:
        logger.exception(f"Server error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
