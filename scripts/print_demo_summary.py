from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.drying_optimization.service import get_dry_recommendation
from app.laundry_progress.service import get_laundry_progress_status
from app.laundry_timing.service import LaundryTimingService


LEVEL_LABELS = {
    "high": "높음",
    "medium": "보통",
    "low": "낮음",
}


async def build_summary(scenario_name: str, address: str | None) -> str:
    defaults = get_demo_scenario(scenario_name)
    timing_service = LaundryTimingService()

    progress = get_laundry_progress_status(
        member_id=defaults.member_id,
        wash_status_id=defaults.wash_status_id,
        washer_id=defaults.washer_id,
        conta_level="중",
        wash_status=1,
        current_load_kg=defaults.current_load_kg,
        washer_capacity_kg=defaults.washer_capacity_kg,
        load_variation_kg=defaults.load_variation_kg,
        contamination_sensor_percent=None,
        cycle_elapsed_minutes=defaults.cycle_elapsed_minutes,
        base_cycle_minutes=defaults.base_cycle_minutes,
        final_spin_rpm=defaults.final_spin_rpm,
    )

    timing = await timing_service.build_laundry_recommendation(
        member_id=defaults.member_id,
        washer_id=defaults.washer_id,
        current_weight=defaults.current_load_kg,
        washer_capacity=defaults.washer_capacity_kg,
        hours_since_last_wash=defaults.hours_since_last_wash,
        weight_increase=defaults.weight_increase_kg,
        household_size=defaults.household_size,
        urgent_clothing_count=defaults.urgent_clothing_count,
        basket_sensor_weight_kg=defaults.sensor_load_kg,
        manual_refresh=False,
        forecast_hours=48,
        region=defaults.region,
        address=None,
        address_type="auto",
        nx=None,
        ny=None,
        latitude=None,
        longitude=None,
        mid_land_reg_id=None,
        mid_ta_reg_id=None,
    )

    drying = await get_dry_recommendation(
        member_id=defaults.member_id,
        washer_id=defaults.washer_id,
        region=defaults.region,
        address=address,
        address_type="road" if address else "auto",
        nx=None,
        ny=None,
        latitude=None,
        longitude=None,
        mid_land_reg_id=None,
        mid_ta_reg_id=None,
        laundry_weight_kg=defaults.dry_laundry_weight_kg,
        has_delicate_items=defaults.has_delicate_items,
        needs_fast_dry=defaults.needs_fast_dry,
        has_outdoor_space=defaults.has_outdoor_space,
        has_dryer=defaults.has_dryer,
        odor_sensitive=defaults.odor_sensitive,
        indoor_humidity=defaults.indoor_humidity,
        indoor_temperature=defaults.indoor_temperature,
        airflow_level=defaults.airflow_level,
        dehumidifier_on=defaults.dehumidifier_on,
        final_spin_rpm=defaults.final_spin_rpm,
        pre_spin_weight_kg=None,
        post_spin_weight_kg=None,
    )

    air_quality = drying.weather_info.air_quality
    air_quality_line = "정보 없음"
    if air_quality is not None:
        air_quality_line = (
            f"{air_quality.station_name} / "
            f"PM10 {air_quality.pm10}({air_quality.pm10_grade}), "
            f"PM2.5 {air_quality.pm25}({air_quality.pm25_grade})"
        )

    lines = [
        "=== 세탁 진행 상황 ===",
        f"현재 상태: {progress.current_status}",
        f"진행률: {progress.progress_percent}%",
        f"남은 시간: {progress.remaining_time}분",
        f"예상 종료 시간: {progress.expected_end_time}",
        f"시간 변경 사유: {progress.update_reason}",
        f"단계 안내: {' / '.join(progress.stage_notes)}",
        f"적재량: {progress.sensor_summary.current_load_kg}kg / {progress.sensor_summary.washer_capacity_kg}kg",
        f"적재율: {progress.sensor_summary.load_ratio}%",
        f"부하 변화: {progress.sensor_summary.load_variation_kg}kg",
        "",
        "=== 세탁 타이밍 추천 ===",
        f"추천 결과: {timing.recommendation}",
        f"추천 등급: {LEVEL_LABELS.get(timing.recommend_level, timing.recommend_level)}",
        f"추천 이유: {timing.reason}",
        f"날씨 요약: {timing.weather_summary}",
        f"행동 가이드: {' / '.join(timing.action_items) if timing.action_items else '없음'}",
        "",
        "=== 건조 추천 ===",
        f"위치: {drying.weather_info.location_label}",
        f"추천 방식: {drying.dry_rec_method_name}",
        f"추천 등급: {drying.recommend_level_label}",
        f"추천 문구: {drying.recommendation}",
        f"추천 이유: {drying.reason}",
        f"날씨 요약: {drying.weather_info.weather_summary}",
        f"대기질: {air_quality_line}",
        f"건조 환경: {drying.environment_analysis.preferred_environment_label}",
        f"냄새 위험도: {drying.moisture_estimation.odor_risk_level_label}",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print demo summary.")
    parser.add_argument(
        "--scenario",
        default=DEFAULT_DEMO_SCENARIO,
        help="Demo scenario name",
    )
    parser.add_argument(
        "--address",
        default=None,
        help="Optional address for location-based drying recommendation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(asyncio.run(build_summary(args.scenario, args.address)))


if __name__ == "__main__":
    main()
