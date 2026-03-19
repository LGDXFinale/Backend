from __future__ import annotations

from pydantic import BaseModel, Field


class CareChecklistItemResponse(BaseModel):
    label: str = Field(..., description="Checklist label")
    done: bool = Field(..., description="Whether the item is complete")


class CareContentCardResponse(BaseModel):
    key: str = Field(..., description="Stable content identifier")
    title: str = Field(..., description="Content title")
    summary: str = Field(..., description="Content summary")
    route: str = Field(..., description="Suggested frontend route")


class CareSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    headline: str = Field(..., description="Primary care headline")
    reward_points: int = Field(..., ge=0, description="Prototype reward points")
    checklist: list[CareChecklistItemResponse] = Field(
        ..., description="Care checklist items"
    )
    featured_cards: list[CareContentCardResponse] = Field(
        ..., description="Care content cards"
    )
