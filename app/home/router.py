from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO
from app.home.schemas import HomeSummaryResponse
from app.home.service import HomeSummaryService


router = APIRouter(prefix="/api/home", tags=["home"])
service = HomeSummaryService()


@router.get("/summary", response_model=HomeSummaryResponse)
async def read_home_summary(
    scenario: str = Query(
        DEFAULT_DEMO_SCENARIO,
        description="Demo scenario: single_household or family4_household",
    ),
    member_id: str | None = Query(None, description="Member id"),
    washer_id: str | None = Query(None, description="Washer id"),
    region: str | None = Query(None, description="Region preset name"),
    address: str | None = Query(None, description="Detailed address"),
    address_type: str = Query("auto", description="Address type: auto, road, parcel"),
    nx: int | None = Query(None, description="KMA grid X"),
    ny: int | None = Query(None, description="KMA grid Y"),
    latitude: float | None = Query(None, description="WGS84 latitude"),
    longitude: float | None = Query(None, description="WGS84 longitude"),
    mid_land_reg_id: str | None = Query(
        None, description="KMA mid-term land forecast code"
    ),
    mid_ta_reg_id: str | None = Query(
        None, description="KMA mid-term temperature forecast code"
    ),
    current_load_kg: float | None = Query(
        None, ge=0, description="Current laundry weight"
    ),
    washer_capacity_kg: float | None = Query(
        None, gt=0, description="Washer capacity"
    ),
    load_variation_kg: float | None = Query(
        None, description="Detected load variation"
    ),
    cycle_elapsed_minutes: int | None = Query(
        None, ge=0, description="Elapsed cycle minutes"
    ),
    base_cycle_minutes: int | None = Query(
        None, ge=1, description="Base cycle minutes"
    ),
    final_spin_rpm: int | None = Query(None, ge=0, description="Final spin RPM"),
) -> HomeSummaryResponse:
    try:
        return await service.build_home_summary(
            scenario=scenario,
            member_id=member_id,
            washer_id=washer_id,
            region=region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
            current_load_kg=current_load_kg,
            washer_capacity_kg=washer_capacity_kg,
            load_variation_kg=load_variation_kg,
            cycle_elapsed_minutes=cycle_elapsed_minutes,
            base_cycle_minutes=base_cycle_minutes,
            final_spin_rpm=final_spin_rpm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
