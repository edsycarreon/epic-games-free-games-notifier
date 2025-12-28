"""Data models for Epic Games free games."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class GameStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    EXPIRED = "expired"


class DiscountSetting(BaseModel):
    discount_type: str = Field(alias="discountType")
    # 0 = 100% off (free), 10 = 10% off, etc.
    discount_percentage: int = Field(alias="discountPercentage")

    class Config:
        populate_by_name = True


class PromotionalOffer(BaseModel):
    start_date: datetime = Field(alias="startDate")
    end_date: datetime = Field(alias="endDate")
    discount_setting: DiscountSetting = Field(alias="discountSetting")

    class Config:
        populate_by_name = True

    @property
    def is_active(self) -> bool:
        now = datetime.now(self.start_date.tzinfo)
        return self.start_date <= now < self.end_date

    @property
    def is_upcoming(self) -> bool:
        now = datetime.now(self.start_date.tzinfo)
        return now < self.start_date


class PromotionalOfferGroup(BaseModel):
    """Epic's API nests offers in groups for some reason."""

    promotional_offers: list[PromotionalOffer] = Field(
        default_factory=list, alias="promotionalOffers"
    )

    class Config:
        populate_by_name = True


class Promotions(BaseModel):
    promotional_offers: list[PromotionalOfferGroup] = Field(
        default_factory=list, alias="promotionalOffers"
    )
    upcoming_promotional_offers: list[PromotionalOfferGroup] = Field(
        default_factory=list, alias="upcomingPromotionalOffers"
    )

    class Config:
        populate_by_name = True

    def get_all_offers(self) -> list[PromotionalOffer]:
        """Flatten nested offer groups into a single list."""
        offers = []
        for group in self.promotional_offers:
            offers.extend(group.promotional_offers)
        for group in self.upcoming_promotional_offers:
            offers.extend(group.promotional_offers)
        return offers

    def get_current_offers(self) -> list[PromotionalOffer]:
        offers = []
        for group in self.promotional_offers:
            offers.extend(group.promotional_offers)
        return offers

    def get_upcoming_offers(self) -> list[PromotionalOffer]:
        offers = []
        for group in self.upcoming_promotional_offers:
            offers.extend(group.promotional_offers)
        return offers


class KeyImage(BaseModel):
    type: str
    url: str  # str not HttpUrl - Epic uses custom schemes like com.epicgames.video://


class Seller(BaseModel):
    name: str


class Price(BaseModel):
    total_price: dict = Field(alias="totalPrice")
    line_offers: list = Field(default_factory=list, alias="lineOffers")

    class Config:
        populate_by_name = True

    @property
    def original_price(self) -> int:
        return self.total_price.get("originalPrice", 0)

    @property
    def discount_price(self) -> int:
        return self.total_price.get("discountPrice", 0)

    @property
    def formatted_price(self) -> str:
        return self.total_price.get("fmtPrice", {}).get("originalPrice", "N/A")


class FreeGame(BaseModel):
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
        return self.seller.name

    @property
    def store_url(self) -> str:
        slug = self.product_slug or self.url_slug or self.id
        return f"https://store.epicgames.com/en-US/p/{slug}"

    @property
    def thumbnail_url(self) -> Optional[str]:
        preferred_types = ["Thumbnail", "OfferImageWide", "DieselStoreFrontWide"]
        for img in self.key_images:
            if img.type in preferred_types:
                return img.url
        return self.key_images[0].url if self.key_images else None

    @property
    def current_promotions(self) -> list[PromotionalOffer]:
        if not self.promotions:
            return []
        return [offer for offer in self.promotions.get_all_offers() if offer.is_active]

    @property
    def is_free(self) -> bool:
        """discount_percentage == 0 means 100% off (free)."""
        if not self.promotions:
            return False
        return any(
            offer.discount_setting.discount_percentage == 0
            for offer in self.promotions.get_all_offers()
        )

    @property
    def status(self) -> GameStatus:
        if not self.promotions:
            return GameStatus.EXPIRED

        all_offers = self.promotions.get_all_offers()
        if not all_offers:
            return GameStatus.EXPIRED

        # Only count 100% free offers (discount_percentage == 0), not partial discounts
        for offer in all_offers:
            if offer.discount_setting.discount_percentage == 0:
                if offer.is_active:
                    return GameStatus.ACTIVE
                if offer.is_upcoming:
                    return GameStatus.UPCOMING

        return GameStatus.EXPIRED

    @property
    def available_from(self) -> Optional[datetime]:
        if not self.promotions:
            return None
        all_offers = self.promotions.get_all_offers()
        return all_offers[0].start_date if all_offers else None

    @property
    def available_until(self) -> Optional[datetime]:
        if not self.promotions:
            return None
        all_offers = self.promotions.get_all_offers()
        return all_offers[0].end_date if all_offers else None


class FreeGamesResponse(BaseModel):
    data: dict

    @property
    def games(self) -> list[FreeGame]:
        # API response: data.data.Catalog.searchStore.elements[]
        catalog = self.data.get("data", {}).get("Catalog", {})
        elements = catalog.get("searchStore", {}).get("elements", [])

        games = []
        for element in elements:
            try:
                game = FreeGame(**element)
                if game.status in [GameStatus.ACTIVE, GameStatus.UPCOMING]:
                    games.append(game)
            except Exception:
                continue

        return games

    @property
    def active_games(self) -> list[FreeGame]:
        return [g for g in self.games if g.status == GameStatus.ACTIVE]

    @property
    def upcoming_games(self) -> list[FreeGame]:
        return [g for g in self.games if g.status == GameStatus.UPCOMING]
