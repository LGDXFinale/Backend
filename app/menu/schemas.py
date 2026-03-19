from __future__ import annotations

from pydantic import BaseModel, Field


class MenuLinkResponse(BaseModel):
    key: str = Field(..., description="Stable menu item identifier")
    label: str = Field(..., description="Menu label")
    route: str = Field(..., description="Suggested frontend route")


class MenuSectionResponse(BaseModel):
    title: str = Field(..., description="Menu section title")
    items: list[MenuLinkResponse] = Field(..., description="Menu links")


class MenuSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    profile_name: str = Field(..., description="Display name")
    profile_summary: str = Field(..., description="Short profile summary")
    sections: list[MenuSectionResponse] = Field(..., description="Menu sections")
