"""Main script for Epic Games Free Games notification system."""

import argparse
import logging
import sys
from pathlib import Path

from .api_client import EpicGamesClient
from .config import load_config, setup_logging
from .discord_notifier import DiscordNotifier
from .exceptions import EpicGamesAPIError
from .models import FreeGame

logger = logging.getLogger(__name__)


def format_game_info(game: FreeGame) -> str:
    lines = [
        f"\n{'=' * 60}",
        f"Title: {game.title}",
        f"Publisher: {game.publisher}",
        f"Status: {game.status.value.upper()}",
        f"Description: {game.description[:200]}{'...' if len(game.description) > 200 else ''}",
        f"Store URL: {game.store_url}",
    ]

    if game.available_from:
        lines.append(f"Available From: {game.available_from.strftime('%Y-%m-%d %H:%M UTC')}")

    if game.available_until:
        lines.append(f"Available Until: {game.available_until.strftime('%Y-%m-%d %H:%M UTC')}")

    if game.thumbnail_url:
        lines.append(f"Thumbnail: {game.thumbnail_url}")

    lines.append("=" * 60)

    return "\n".join(lines)


def display_games(games: list[FreeGame], title: str) -> None:
    print(f"\n{'#' * 60}")
    print(f"# {title}")
    print(f"{'#' * 60}")

    if not games:
        print("No games found.")
        return

    for game in games:
        print(format_game_info(game))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch free games from Epic Games Store"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config.yaml file",
        default=Path.cwd() / "config.yaml",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="Show only currently active free games",
    )
    parser.add_argument(
        "--upcoming-only",
        action="store_true",
        help="Show only upcoming free games",
    )
    parser.add_argument(
        "--send-discord",
        action="store_true",
        help="Send notifications to Discord (requires configuration)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from config",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as exc:
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return 1

    if args.log_level:
        config.logging.level = args.log_level

    setup_logging(config.logging)
    logger.info("Starting Epic Games Free Games Notifier")

    try:
        with EpicGamesClient(
            locale=config.epic_games.locale,
            country=config.epic_games.country,
            allow_countries=config.epic_games.allow_countries,
        ) as client:
            if args.active_only:
                games = client.get_active_games()
                display_games(games, "CURRENTLY FREE GAMES")
            elif args.upcoming_only:
                games = client.get_upcoming_games()
                display_games(games, "UPCOMING FREE GAMES")
            else:
                all_games = client.get_free_games()
                active_games = [g for g in all_games if g.status.value == "active"]
                upcoming_games = [g for g in all_games if g.status.value == "upcoming"]

                display_games(active_games, "CURRENTLY FREE GAMES")
                display_games(upcoming_games, "UPCOMING FREE GAMES")

                games = all_games

            if args.send_discord and config.discord.enabled:
                notifier = DiscordNotifier(config.discord)

                if args.active_only:
                    if games:
                        notifier.send_multiple_games_notification(
                            games,
                            "🎮 Free Games Available Now!",
                            config.notifications.include_game_images,
                        )
                elif args.upcoming_only:
                    if games:
                        notifier.send_multiple_games_notification(
                            games,
                            "📅 Upcoming Free Games",
                            config.notifications.include_game_images,
                        )
                else:
                    if active_games and config.notifications.notify_current_games:
                        notifier.send_multiple_games_notification(
                            active_games,
                            "🎮 Free Games Available Now!",
                            config.notifications.include_game_images,
                        )
                    if upcoming_games and config.notifications.notify_upcoming_games:
                        notifier.send_multiple_games_notification(
                            upcoming_games,
                            "📅 Upcoming Free Games",
                            config.notifications.include_game_images,
                        )

            logger.info(f"Successfully processed {len(games)} games")

    except EpicGamesAPIError as exc:
        logger.error(f"API error: {exc}")
        print(f"Error fetching games: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
        return 130
    except Exception as exc:
        logger.exception(f"Unexpected error: {exc}")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
