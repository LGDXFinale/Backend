from __future__ import annotations

from pydantic import BaseModel, Field

from app.screen_schemas import ScreenActionResponse, ScreenMetaResponse


class MenuLinkResponse(BaseModel):
    key: str = Field(..., description="Stable menu item identifier")
    label: str = Field(..., description="Menu label")
    icon_key: str = Field(..., description="Menu icon key")
    route: str = Field(..., description="Suggested frontend route")
    badge: str | None = Field(None, description="Optional badge text")


class MenuSectionResponse(BaseModel):
    key: str = Field(..., description="Stable section identifier")
    title: str = Field(..., description="Menu section title")
    items: list[MenuLinkResponse] = Field(..., description="Menu links")


class MenuSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    screen: ScreenMetaResponse = Field(..., description="Menu screen metadata")
    profile_name: str = Field(..., description="Display name")
    profile_summary: str = Field(..., description="Short profile summary")
    quick_actions: list[ScreenActionResponse] = Field(
        ..., description="Frequently used menu actions"
    )
    sections: list[MenuSectionResponse] = Field(..., description="Menu sections")
