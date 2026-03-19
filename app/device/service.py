from __future__ import annotations

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.device.schemas import (
    DeviceActionResponse,
    DeviceInfoCardResponse,
    DeviceSummaryResponse,
)
from app.home.service import DEFAULT_CONTA_LEVEL
from app.laundry_progress.service import get_laundry_progress_status


class DeviceSummaryService:
    def build_device_summary(
        self,
        *,
        scenario: str = DEFAULT_DEMO_SCENARIO,
        member_id: str | None = None,
        washer_id: str | None = None,
    ) -> DeviceSummaryResponse:
        defaults = get_demo_scenario(scenario)
        progress = get_laundry_progress_status(
            member_id=member_id or defaults.member_id,
            wash_status_id=defaults.wash_status_id,
            washer_id=washer_id or defaults.washer_id,
            conta_level=DEFAULT_CONTA_LEVEL,
            wash_status=1,
            current_load_kg=defaults.current_load_kg,
            washer_capacity_kg=defaults.washer_capacity_kg,
            load_variation_kg=defaults.load_variation_kg,
            contamination_sensor_percent=None,
            cycle_elapsed_minutes=defaults.cycle_elapsed_minutes,
            base_cycle_minutes=defaults.base_cycle_minutes,
            final_spin_rpm=defaults.final_spin_rpm,
        )
        return DeviceSummaryResponse(
            generated_at=progress.generated_at,
            member_id=progress.member_id,
            washer_id=progress.washer_id,
            device_name="LG ThinQ Washer",
            connection_status="연결됨",
            status_image_key="device_connected",
            last_synced_at=progress.generated_at,
            cards=[
                DeviceInfoCardResponse(
                    key="load",
                    title="현재 적재량",
                    value=f"{progress.sensor_summary.current_load_kg:.1f}kg / {progress.sensor_summary.washer_capacity_kg:.1f}kg",
                    summary=f"적재율 {progress.sensor_summary.load_ratio}%",
                ),
                DeviceInfoCardResponse(
                    key="status",
                    title="현재 상태",
                    value=progress.current_status,
                    summary=progress.update_reason,
                ),
                DeviceInfoCardResponse(
                    key="finish",
                    title="예상 종료",
                    value=progress.expected_end_time,
                    summary=f"남은 시간 {progress.remaining_time}분",
                ),
            ],
            actions=[
                DeviceActionResponse(
                    key="progress",
                    label="세탁 진행 보기",
                    route="/wash/progress",
                ),
                DeviceActionResponse(
                    key="timing",
                    label="세탁 타이밍 보기",
                    route="/wash/timing",
                ),
            ],
        )
