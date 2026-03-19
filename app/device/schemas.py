from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceInfoCardResponse(BaseModel):
    key: str = Field(..., description="Stable card identifier")
    title: str = Field(..., description="Card title")
    value: str = Field(..., description="Primary value")
    summary: str = Field(..., description="Short card summary")


class DeviceActionResponse(BaseModel):
    key: str = Field(..., description="Action identifier")
    label: str = Field(..., description="Action label")
    route: str = Field(..., description="Suggested frontend route")


class DeviceSummaryResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    washer_id: str = Field(..., description="Washer id")
    device_name: str = Field(..., description="Device display name")
    connection_status: str = Field(..., description="Connection status label")
    status_image_key: str = Field(..., description="Device status image key")
    last_synced_at: str = Field(..., description="Last sync timestamp")
    cards: list[DeviceInfoCardResponse] = Field(..., description="Device info cards")
    actions: list[DeviceActionResponse] = Field(..., description="Suggested actions")
