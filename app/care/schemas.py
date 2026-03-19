from __future__ import annotations

from pydantic import BaseModel, Field

from app.screen_schemas import ScreenMetaResponse


class CareChecklistItemResponse(BaseModel):
    label: str = Field(..., description="Checklist label")
    done: bool = Field(..., description="Whether the item is complete")
    priority: str = Field(..., description="Checklist priority label")


class CareContentCardResponse(BaseModel):
    key: str = Field(..., description="Stable content identifier")
    category: str = Field(..., description="Content category")
    image_key: str = Field(..., description="Suggested image key")
    title: str = Field(..., description="Content title")
    summary: str = Field(..., description="Content summary")
    route: str = Field(..., description="Suggested frontend route")
    cta_label: str = Field(..., description="Suggested button label")


class CareSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    screen: ScreenMetaResponse = Field(..., description="Care screen metadata")
    headline: str = Field(..., description="Primary care headline")
    summary: str = Field(..., description="Short care summary")
    reward_points: int = Field(..., ge=0, description="Prototype reward points")
    checklist: list[CareChecklistItemResponse] = Field(
        ..., description="Care checklist items"
    )
    featured_cards: list[CareContentCardResponse] = Field(
        ..., description="Care content cards"
    )
