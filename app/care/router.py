from __future__ import annotations

from fastapi import APIRouter, Query

from app.care.schemas import CareSummaryResponse
from app.care.service import CareSummaryService
from app.demo_defaults import DEFAULT_DEMO_SCENARIO


router = APIRouter(prefix="/api/care", tags=["care"])
service = CareSummaryService()


@router.get("/summary", response_model=CareSummaryResponse)
def read_care_summary(
    scenario: str = Query(
        DEFAULT_DEMO_SCENARIO,
        description="Demo scenario: single_household or family4_household",
    ),
    member_id: str | None = Query(None, description="Member id"),
) -> CareSummaryResponse:
    return service.build_care_summary(
        scenario=scenario,
        member_id=member_id,
    )
