from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ScreenActionStyle = Literal["primary", "secondary", "ghost"]


class ScreenActionResponse(BaseModel):
    key: str = Field(..., description="Stable action identifier")
    label: str = Field(..., description="Action label")
    route: str = Field(..., description="Suggested frontend route")
    style: ScreenActionStyle = Field(..., description="Suggested action button style")
    badge: str | None = Field(None, description="Optional action badge")


class ScreenMetaResponse(BaseModel):
    title: str = Field(..., description="Screen title")
    subtitle: str | None = Field(None, description="Screen subtitle")
    route: str = Field(..., description="Screen route")
    active_tab: str = Field(..., description="Currently active bottom tab")
    primary_action: ScreenActionResponse | None = Field(
        None, description="Primary suggested screen action"
    )
    secondary_action: ScreenActionResponse | None = Field(
        None, description="Secondary suggested screen action"
    )
