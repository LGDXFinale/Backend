from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO
from app.device.schemas import DeviceSummaryResponse
from app.device.service import DeviceSummaryService


router = APIRouter(prefix="/api/device", tags=["device"])
service = DeviceSummaryService()


@router.get("/summary", response_model=DeviceSummaryResponse)
def read_device_summary(
    scenario: str = Query(
        DEFAULT_DEMO_SCENARIO,
        description="Demo scenario: single_household or family4_household",
    ),
    member_id: str | None = Query(None, description="Member id"),
    washer_id: str | None = Query(None, description="Washer id"),
) -> DeviceSummaryResponse:
    return service.build_device_summary(
        scenario=scenario,
        member_id=member_id,
        washer_id=washer_id,
    )
