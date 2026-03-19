from __future__ import annotations

from pydantic import BaseModel, Field

from app.screen_schemas import ScreenActionResponse, ScreenMetaResponse


class DeviceInfoCardResponse(BaseModel):
    key: str = Field(..., description="Stable card identifier")
    title: str = Field(..., description="Card title")
    icon_key: str = Field(..., description="Card icon key")
    value: str = Field(..., description="Primary value")
    summary: str = Field(..., description="Short card summary")
    route: str | None = Field(None, description="Suggested deep link route")


class DeviceSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    washer_id: str = Field(..., description="Washer id")
    screen: ScreenMetaResponse = Field(..., description="Device screen metadata")
    device_name: str = Field(..., description="Device display name")
    connection_status: str = Field(..., description="Connection status label")
    status_image_key: str = Field(..., description="Device status image key")
    last_synced_at: str = Field(..., description="Last sync timestamp")
    highlights: list[str] = Field(..., description="Top screen highlights")
    cards: list[DeviceInfoCardResponse] = Field(..., description="Device info cards")
    actions: list[ScreenActionResponse] = Field(..., description="Suggested actions")
