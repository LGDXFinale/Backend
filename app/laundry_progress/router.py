from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import (
    DEMO_BASE_CYCLE_MINUTES,
    DEMO_CYCLE_ELAPSED_MINUTES,
    DEMO_CURRENT_LOAD_KG,
    DEMO_FINAL_SPIN_RPM,
    DEMO_LOAD_VARIATION_KG,
    DEMO_MEMBER_ID,
    DEMO_WASHER_CAPACITY_KG,
    DEMO_WASHER_ID,
    DEMO_WASH_STATUS_ID,
)
from app.laundry_progress.schemas import LaundryProgressResponse
from app.laundry_progress.service import get_laundry_progress_status


router = APIRouter(prefix="/api/laundry-progress", tags=["laundry-progress"])


@router.get("/status", response_model=LaundryProgressResponse)
def get_laundry_progress(
    member_id: str = Query(DEMO_MEMBER_ID, description="회원 ID"),
    wash_status_id: str = Query(DEMO_WASH_STATUS_ID, description="세탁 상태 ID"),
    washer_id: str = Query(DEMO_WASHER_ID, description="세탁기 ID"),
    conta_level: str = Query("중", description="초기 오염도"),
    wash_status: int = Query(1, ge=0, le=4, description="세탁 상태 코드"),
    current_load_kg: float = Query(DEMO_CURRENT_LOAD_KG, ge=0, description="현재 세탁물 무게"),
    washer_capacity_kg: float = Query(DEMO_WASHER_CAPACITY_KG, gt=0, description="세탁기 용량"),
    load_variation_kg: float = Query(DEMO_LOAD_VARIATION_KG, description="세탁 중 감지된 부하 변화량"),
    contamination_sensor_percent: int | None = Query(None, ge=0, le=100, description="센서 오염 잔량"),
    cycle_elapsed_minutes: int = Query(DEMO_CYCLE_ELAPSED_MINUTES, ge=0, description="현재까지 진행 시간"),
    base_cycle_minutes: int = Query(DEMO_BASE_CYCLE_MINUTES, ge=1, description="기본 세탁 시간"),
    final_spin_rpm: int | None = Query(DEMO_FINAL_SPIN_RPM, ge=0, description="현재 또는 마지막 탈수 RPM"),
) -> LaundryProgressResponse:
    return get_laundry_progress_status(
        member_id=member_id,
        wash_status_id=wash_status_id,
        washer_id=washer_id,
        conta_level=conta_level,
        wash_status=wash_status,
        current_load_kg=current_load_kg,
        washer_capacity_kg=washer_capacity_kg,
        load_variation_kg=load_variation_kg,
        contamination_sensor_percent=contamination_sensor_percent,
        cycle_elapsed_minutes=cycle_elapsed_minutes,
        base_cycle_minutes=base_cycle_minutes,
        final_spin_rpm=final_spin_rpm,
    )
