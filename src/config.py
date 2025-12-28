"""Configuration management for the application."""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings


class EpicGamesConfig(BaseModel):
    locale: str = "en-US"
    country: str = "US"
    allow_countries: str = "US"


class DiscordConfig(BaseModel):
    enabled: bool = False
    webhook_url: Optional[str] = None
    mention_role_id: Optional[str] = None


class NotificationConfig(BaseModel):
    notify_current_games: bool = True
    notify_upcoming_games: bool = True
    include_game_images: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "epic_games_notifier.log"


class Config(BaseSettings):
    epic_games: EpicGamesConfig = Field(default_factory=EpicGamesConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Env vars override YAML config
    discord_webhook_url: Optional[str] = Field(None, validation_alias="DISCORD_WEBHOOK_URL")
    discord_mention_role_id: Optional[str] = Field(
        None, validation_alias="DISCORD_MENTION_ROLE_ID"
    )
    epic_locale: Optional[str] = Field(None, validation_alias="EPIC_LOCALE")
    epic_country: Optional[str] = Field(None, validation_alias="EPIC_COUNTRY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def apply_env_overrides(self) -> None:
        if self.discord_webhook_url:
            self.discord.webhook_url = self.discord_webhook_url
            self.discord.enabled = True

        if self.discord_mention_role_id:
            self.discord.mention_role_id = self.discord_mention_role_id

        if self.epic_locale:
            self.epic_games.locale = self.epic_locale

        if self.epic_country:
            self.epic_games.country = self.epic_country
            self.epic_games.allow_countries = self.epic_country


def load_config(config_path: Optional[Path] = None) -> Config:
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    if not config_path.exists():
        logging.warning(f"Config file not found at {config_path}, using defaults")
        config = Config()
        config.apply_env_overrides()
        return config

    try:
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file: {exc}") from exc

    try:
        config = Config(**yaml_data)
        config.apply_env_overrides()
        return config
    except Exception as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc


def setup_logging(config: LoggingConfig) -> None:
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    formatter = logging.Formatter(config.format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if config.file:
        file_handler = logging.FileHandler(config.file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
