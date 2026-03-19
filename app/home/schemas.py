from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


HomeCardLevel = Literal["low", "medium", "high"] | None


class HomeNavigationItemResponse(BaseModel):
    key: str = Field(..., description="Stable navigation identifier")
    label: str = Field(..., description="Navigation label")
    route: str = Field(..., description="Suggested frontend route")
    icon_key: str = Field(..., description="UI icon key")
    badge: str | None = Field(None, description="Optional badge text")


class HomeSummaryCardResponse(BaseModel):
    key: str = Field(..., description="Stable card identifier")
    title: str = Field(..., description="Card title")
    headline: str = Field(..., description="Primary headline")
    summary: str = Field(..., description="Short summary for the card")
    level: HomeCardLevel = Field(None, description="Card emphasis level")
    badge: str | None = Field(None, description="Small badge label")
    status_image_key: str = Field(..., description="UI image/status key")
    updated_at: str = Field(..., description="Timestamp for the card")
    primary_value: str | None = Field(None, description="Primary quick value")
    secondary_value: str | None = Field(None, description="Secondary quick value")
    route: str = Field(..., description="Suggested frontend route")
    action_items: list[str] = Field(..., description="Suggested user actions")


class HomeSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    washer_id: str = Field(..., description="Washer id")
    location_label: str | None = Field(None, description="Resolved location label")
    timing: HomeSummaryCardResponse = Field(..., description="Laundry timing summary")
    progress: HomeSummaryCardResponse = Field(..., description="Laundry progress summary")
    drying: HomeSummaryCardResponse = Field(..., description="Drying recommendation summary")
    shortcuts: list[HomeNavigationItemResponse] = Field(
        ..., description="Prototype quick links from the home screen"
    )
    tabs: list[HomeNavigationItemResponse] = Field(
        ..., description="Bottom tab navigation metadata"
    )
    cards: list[HomeSummaryCardResponse] = Field(..., description="Ordered home cards")
