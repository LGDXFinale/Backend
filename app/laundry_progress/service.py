from __future__ import annotations

from datetime import datetime, timedelta

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
from app.laundry_progress.schemas import (
    LaundryProgressResponse,
    LaundryProgressSensorSummaryResponse,
)


STATUS_MAP = {
    0: {"label": "대기", "status_image_key": "waiting", "baseline_progress": 0},
    1: {"label": "세탁중", "status_image_key": "washing", "baseline_progress": 35},
    2: {"label": "헹굼중", "status_image_key": "rinsing", "baseline_progress": 65},
    3: {"label": "탈수중", "status_image_key": "spinning", "baseline_progress": 88},
    4: {"label": "종료", "status_image_key": "done", "baseline_progress": 100},
}

CONTA_BASE_REMAINING = {
    "상": {0: 100, 1: 70, 2: 35, 3: 15, 4: 0},
    "중": {0: 100, 1: 55, 2: 25, 3: 10, 4: 0},
    "하": {0: 100, 1: 40, 2: 18, 3: 8, 4: 0},
}


def get_laundry_progress_status(
    *,
    member_id: str = DEMO_MEMBER_ID,
    wash_status_id: str = DEMO_WASH_STATUS_ID,
    washer_id: str = DEMO_WASHER_ID,
    conta_level: str = "중",
    wash_status: int = 1,
    current_load_kg: float = DEMO_CURRENT_LOAD_KG,
    washer_capacity_kg: float = DEMO_WASHER_CAPACITY_KG,
    load_variation_kg: float = DEMO_LOAD_VARIATION_KG,
    contamination_sensor_percent: int | None = None,
    cycle_elapsed_minutes: int = DEMO_CYCLE_ELAPSED_MINUTES,
    base_cycle_minutes: int = DEMO_BASE_CYCLE_MINUTES,
    final_spin_rpm: int | None = DEMO_FINAL_SPIN_RPM,
) -> LaundryProgressResponse:
    now = datetime.now()

    load_ratio = round(min((current_load_kg / washer_capacity_kg) * 100, 100), 2)
    dynamic_total_minutes = _calculate_dynamic_total_minutes(
        base_cycle_minutes=base_cycle_minutes,
        load_ratio=load_ratio,
        load_variation_kg=load_variation_kg,
        conta_level=conta_level,
        final_spin_rpm=final_spin_rpm,
    )
    progress_percent = _calculate_progress_percent(
        wash_status=wash_status,
        cycle_elapsed_minutes=cycle_elapsed_minutes,
        dynamic_total_minutes=dynamic_total_minutes,
    )
    remaining_time = max(dynamic_total_minutes - cycle_elapsed_minutes, 0)
    expected_end_time = (now + timedelta(minutes=remaining_time)).strftime("%Y-%m-%d %H:%M:%S")
    conta_percent = _calculate_remaining_contamination(
        conta_level=conta_level,
        wash_status=wash_status,
        contamination_sensor_percent=contamination_sensor_percent,
    )
    status_info = STATUS_MAP.get(
        wash_status,
        {"label": "알 수 없음", "status_image_key": "unknown", "baseline_progress": progress_percent},
    )
    update_reason = _build_update_reason(
        load_ratio=load_ratio,
        load_variation_kg=load_variation_kg,
        final_spin_rpm=final_spin_rpm,
        base_cycle_minutes=base_cycle_minutes,
        dynamic_total_minutes=dynamic_total_minutes,
    )
    stage_notes = _build_stage_notes(
        wash_status=wash_status,
        conta_percent=conta_percent,
        load_variation_kg=load_variation_kg,
    )

    return LaundryProgressResponse(
        generated_at=now.isoformat(timespec="seconds"),
        member_id=member_id,
        wash_status_id=wash_status_id,
        washer_id=washer_id,
        conta_level=conta_level,  # type: ignore[arg-type]
        wash_status=wash_status,
        time_info=now.strftime("%Y-%m-%d %H:%M:%S"),
        current_status=status_info["label"],
        remaining_time=remaining_time,
        expected_end_time=expected_end_time,
        progress_percent=progress_percent,
        conta_percent=conta_percent,
        status_image_key=status_info["status_image_key"],
        elapsed_minutes=cycle_elapsed_minutes,
        base_cycle_minutes=base_cycle_minutes,
        dynamic_total_minutes=dynamic_total_minutes,
        load_variation_detected=abs(load_variation_kg) >= 0.2,
        update_reason=update_reason,
        stage_notes=stage_notes,
        sensor_summary=LaundryProgressSensorSummaryResponse(
            current_load_kg=current_load_kg,
            washer_capacity_kg=washer_capacity_kg,
            load_ratio=load_ratio,
            load_variation_kg=load_variation_kg,
            contamination_sensor_percent=contamination_sensor_percent,
            final_spin_rpm=final_spin_rpm,
        ),
    )


def _calculate_dynamic_total_minutes(
    *,
    base_cycle_minutes: int,
    load_ratio: float,
    load_variation_kg: float,
    conta_level: str,
    final_spin_rpm: int | None,
) -> int:
    adjustment = 0
    if load_ratio >= 85:
        adjustment += 14
    elif load_ratio >= 65:
        adjustment += 8

    if abs(load_variation_kg) >= 0.5:
        adjustment += 6
    elif abs(load_variation_kg) >= 0.2:
        adjustment += 3

    if conta_level == "상":
        adjustment += 8
    elif conta_level == "중":
        adjustment += 4

    if final_spin_rpm is not None and final_spin_rpm < 700:
        adjustment += 4

    return max(base_cycle_minutes + adjustment, 1)


def _calculate_progress_percent(
    *,
    wash_status: int,
    cycle_elapsed_minutes: int,
    dynamic_total_minutes: int,
) -> int:
    elapsed_based = round(min((cycle_elapsed_minutes / dynamic_total_minutes) * 100, 100))
    baseline = STATUS_MAP.get(wash_status, {}).get("baseline_progress", elapsed_based)
    return min(100, max(elapsed_based, baseline if wash_status < 4 else 100))


def _calculate_remaining_contamination(
    *,
    conta_level: str,
    wash_status: int,
    contamination_sensor_percent: int | None,
) -> int:
    if contamination_sensor_percent is not None:
        return contamination_sensor_percent
    mapping = CONTA_BASE_REMAINING.get(conta_level, CONTA_BASE_REMAINING["중"])
    return mapping.get(wash_status, 0)


def _build_update_reason(
    *,
    load_ratio: float,
    load_variation_kg: float,
    final_spin_rpm: int | None,
    base_cycle_minutes: int,
    dynamic_total_minutes: int,
) -> str:
    if dynamic_total_minutes == base_cycle_minutes:
        return "현재 센서 기준으로 기본 코스 시간과 큰 차이 없이 진행 중입니다."
    reasons: list[str] = []
    if load_ratio >= 65:
        reasons.append("적재율이 높음")
    if abs(load_variation_kg) >= 0.2:
        reasons.append("세탁 중 부하 변화 감지")
    if final_spin_rpm is not None and final_spin_rpm < 700:
        reasons.append("낮은 탈수 RPM")
    if not reasons:
        return "세탁 부하와 오염도 조건을 반영해 예상 완료 시간을 미세 조정했습니다."
    return ", ".join(reasons) + "으로 예상 완료 시간이 재계산되었습니다."


def _build_stage_notes(
    *,
    wash_status: int,
    conta_percent: int,
    load_variation_kg: float,
) -> list[str]:
    notes: list[str] = []
    if wash_status == 1:
        notes.append("세탁 단계에서는 오염 제거율이 가장 크게 변합니다.")
    elif wash_status == 2:
        notes.append("헹굼 단계에서는 세제 잔여물과 오염 잔량이 함께 줄어듭니다.")
    elif wash_status == 3:
        notes.append("탈수 단계에서는 오염도보다 수분 제거가 중심입니다.")
    elif wash_status == 4:
        notes.append("세탁이 종료되어 추가 재계산은 필요하지 않습니다.")

    notes.append(f"현재 추정 남은 오염도는 {conta_percent}%입니다.")
    if abs(load_variation_kg) >= 0.2:
        notes.append("부하 변화가 감지되어 잔여 시간 예측을 조정했습니다.")
    return notes
