from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO
from app.menu.schemas import MenuSummaryResponse
from app.menu.service import MenuSummaryService


router = APIRouter(prefix="/api/menu", tags=["menu"])
service = MenuSummaryService()


@router.get("/summary", response_model=MenuSummaryResponse)
def read_menu_summary(
    scenario: str = Query(
        DEFAULT_DEMO_SCENARIO,
        description="Demo scenario: single_household or family4_household",
    ),
    member_id: str | None = Query(None, description="Member id"),
) -> MenuSummaryResponse:
    return service.build_menu_summary(
        scenario=scenario,
        member_id=member_id,
    )
