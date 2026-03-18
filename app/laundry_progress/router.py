from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.laundry_progress.schemas import LaundryProgressResponse
from app.laundry_progress.service import get_laundry_progress_status


router = APIRouter(prefix="/api/laundry-progress", tags=["laundry-progress"])


@router.get("/status", response_model=LaundryProgressResponse)
def get_laundry_progress(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    member_id: str | None = Query(None, description="Member ID"),
    wash_status_id: str | None = Query(None, description="Wash status ID"),
    washer_id: str | None = Query(None, description="Washer ID"),
    conta_level: str | None = Query(None, description="Initial contamination level"),
    wash_status: int | None = Query(None, ge=0, le=4, description="Wash status code"),
    current_load_kg: float | None = Query(None, ge=0, description="Current laundry weight"),
    washer_capacity_kg: float | None = Query(None, gt=0, description="Washer capacity"),
    load_variation_kg: float | None = Query(None, description="Detected load variation"),
    contamination_sensor_percent: int | None = Query(None, ge=0, le=100, description="Contamination sensor percent"),
    cycle_elapsed_minutes: int | None = Query(None, ge=0, description="Elapsed cycle minutes"),
    base_cycle_minutes: int | None = Query(None, ge=1, description="Base cycle minutes"),
    final_spin_rpm: int | None = Query(None, ge=0, description="Final spin RPM"),
) -> LaundryProgressResponse:
    defaults = get_demo_scenario(scenario)

    return get_laundry_progress_status(
        member_id=member_id or defaults.member_id,
        wash_status_id=wash_status_id or defaults.wash_status_id,
        washer_id=washer_id or defaults.washer_id,
        conta_level=conta_level or "중",
        wash_status=wash_status if wash_status is not None else 1,
        current_load_kg=current_load_kg if current_load_kg is not None else defaults.current_load_kg,
        washer_capacity_kg=washer_capacity_kg if washer_capacity_kg is not None else defaults.washer_capacity_kg,
        load_variation_kg=load_variation_kg if load_variation_kg is not None else defaults.load_variation_kg,
        contamination_sensor_percent=contamination_sensor_percent,
        cycle_elapsed_minutes=cycle_elapsed_minutes if cycle_elapsed_minutes is not None else defaults.cycle_elapsed_minutes,
        base_cycle_minutes=base_cycle_minutes if base_cycle_minutes is not None else defaults.base_cycle_minutes,
        final_spin_rpm=final_spin_rpm if final_spin_rpm is not None else defaults.final_spin_rpm,
    )
