"""Data models for Epic Games free games."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class GameStatus(str, Enum):
    """Status of a free game promotion."""

    ACTIVE = "active"
    UPCOMING = "upcoming"
    EXPIRED = "expired"


class DiscountSetting(BaseModel):
    """Discount settings for a promotional offer."""

    discount_type: str = Field(alias="discountType")
    discount_percentage: int = Field(alias="discountPercentage")

    class Config:
        populate_by_name = True


class PromotionalOffer(BaseModel):
    """Individual promotional offer with dates and discount info."""

    start_date: datetime = Field(alias="startDate")
    end_date: datetime = Field(alias="endDate")
    discount_setting: DiscountSetting = Field(alias="discountSetting")

    class Config:
        populate_by_name = True

    @property
    def is_active(self) -> bool:
        """Check if the offer is currently active."""
        now = datetime.now(self.start_date.tzinfo)
        return self.start_date <= now < self.end_date

    @property
    def is_upcoming(self) -> bool:
        """Check if the offer is upcoming."""
        now = datetime.now(self.start_date.tzinfo)
        return now < self.start_date


class PromotionalOfferGroup(BaseModel):
    """Group of promotional offers (Epic's API nests offers in this structure)."""

    promotional_offers: list[PromotionalOffer] = Field(
        default_factory=list, alias="promotionalOffers"
    )

    class Config:
        populate_by_name = True


class Promotions(BaseModel):
    """Container for promotional offers."""

    promotional_offers: list[PromotionalOfferGroup] = Field(
        default_factory=list, alias="promotionalOffers"
    )
    upcoming_promotional_offers: list[PromotionalOfferGroup] = Field(
        default_factory=list, alias="upcomingPromotionalOffers"
    )

    class Config:
        populate_by_name = True

    def get_all_offers(self) -> list[PromotionalOffer]:
        """Flatten all promotional offers from groups."""
        offers = []
        for group in self.promotional_offers:
            offers.extend(group.promotional_offers)
        for group in self.upcoming_promotional_offers:
            offers.extend(group.promotional_offers)
        return offers

    def get_current_offers(self) -> list[PromotionalOffer]:
        """Get all current promotional offers."""
        offers = []
        for group in self.promotional_offers:
            offers.extend(group.promotional_offers)
        return offers

    def get_upcoming_offers(self) -> list[PromotionalOffer]:
        """Get all upcoming promotional offers."""
        offers = []
        for group in self.upcoming_promotional_offers:
            offers.extend(group.promotional_offers)
        return offers


class KeyImage(BaseModel):
    """Game image information."""

    type: str
    url: str  # Changed from HttpUrl to str to support video URLs like com.epicgames.video://


class Seller(BaseModel):
    """Seller/Publisher information."""

    name: str


class Price(BaseModel):
    """Price information for a game."""

    total_price: dict = Field(alias="totalPrice")
    line_offers: list = Field(default_factory=list, alias="lineOffers")

    class Config:
        populate_by_name = True

    @property
    def original_price(self) -> int:
        """Get original price in cents."""
        return self.total_price.get("originalPrice", 0)

    @property
    def discount_price(self) -> int:
        """Get discounted price in cents."""
        return self.total_price.get("discountPrice", 0)

    @property
    def formatted_price(self) -> str:
        """Get formatted price string."""
        return self.total_price.get("fmtPrice", {}).get("originalPrice", "N/A")


class FreeGame(BaseModel):
    """Model representing a free game from Epic Games Store."""

    title: str
    description: str
    id: str
    namespace: str
    seller: Seller
    product_slug: Optional[str] = Field(None, alias="productSlug")
    url_slug: Optional[str] = Field(None, alias="urlSlug")
    key_images: list[KeyImage] = Field(default_factory=list, alias="keyImages")
    price: Optional[Price] = None
    promotions: Optional[Promotions] = None
    effective_date: datetime = Field(alias="effectiveDate")

    class Config:
        populate_by_name = True

    @property
    def publisher(self) -> str:
        """Get publisher name."""
        return self.seller.name

    @property
    def store_url(self) -> str:
        """Get the Epic Games Store URL for this game."""
        slug = self.product_slug or self.url_slug or self.id
        return f"https://store.epicgames.com/en-US/p/{slug}"

    @property
    def thumbnail_url(self) -> Optional[str]:
        """Get thumbnail image URL."""
        for img in self.key_images:
            if img.type in ["Thumbnail", "OfferImageWide", "DieselStoreFrontWide"]:
                return img.url
        return self.key_images[0].url if self.key_images else None

    @property
    def current_promotions(self) -> list[PromotionalOffer]:
        """Get currently active promotional offers."""
        if not self.promotions:
            return []
        all_offers = self.promotions.get_all_offers()
        return [offer for offer in all_offers if offer.is_active]

    @property
    def is_free(self) -> bool:
        """Check if the game is 100% free (not just discounted)."""
        if not self.promotions:
            return False
        all_offers = self.promotions.get_all_offers()
        return any(offer.discount_setting.discount_percentage == 0 for offer in all_offers)

    @property
    def status(self) -> GameStatus:
        """Determine the current status of the game promotion."""
        if not self.promotions:
            return GameStatus.EXPIRED

        all_offers = self.promotions.get_all_offers()
        if not all_offers:
            return GameStatus.EXPIRED

        # Only consider 100% free games (not just discounted)
        for offer in all_offers:
            if offer.discount_setting.discount_percentage == 0:
                if offer.is_active:
                    return GameStatus.ACTIVE
                if offer.is_upcoming:
                    return GameStatus.UPCOMING

        return GameStatus.EXPIRED

    @property
    def available_from(self) -> Optional[datetime]:
        """Get the start date of the promotion."""
        if not self.promotions:
            return None
        all_offers = self.promotions.get_all_offers()
        if not all_offers:
            return None
        return all_offers[0].start_date

    @property
    def available_until(self) -> Optional[datetime]:
        """Get the end date of the promotion."""
        if not self.promotions:
            return None
        all_offers = self.promotions.get_all_offers()
        if not all_offers:
            return None
        return all_offers[0].end_date


class FreeGamesResponse(BaseModel):
    """Response model for free games API."""

    data: dict

    @property
    def games(self) -> list[FreeGame]:
        """Extract and parse free games from the response."""
        catalog = self.data.get("data", {}).get("Catalog", {})
        search_store = catalog.get("searchStore", {})
        elements = search_store.get("elements", [])

        games = []
        for element in elements:
            try:
                game = FreeGame(**element)
                # Only include games that have active or upcoming promotions
                if game.status in [GameStatus.ACTIVE, GameStatus.UPCOMING]:
                    games.append(game)
            except Exception:
                # Skip games that fail validation
                continue

        return games

    @property
    def active_games(self) -> list[FreeGame]:
        """Get currently active free games."""
        return [game for game in self.games if game.status == GameStatus.ACTIVE]

    @property
    def upcoming_games(self) -> list[FreeGame]:
        """Get upcoming free games."""
        return [game for game in self.games if game.status == GameStatus.UPCOMING]
