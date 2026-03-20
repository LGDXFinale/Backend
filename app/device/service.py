from __future__ import annotations

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.device.schemas import DeviceInfoCardResponse, DeviceSummaryResponse
from app.home.service import DEFAULT_CONTA_LEVEL
from app.laundry_progress.service import get_laundry_progress_status
from app.screen_schemas import ScreenActionResponse, ScreenMetaResponse


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
            screen=ScreenMetaResponse(
                title="디바이스",
                subtitle="연결된 세탁기 상태와 바로가기",
                route="/device",
                active_tab="device",
                primary_action=ScreenActionResponse(
                    key="open_progress",
                    label="세탁 진행 보기",
                    route="/wash/progress",
                    style="primary",
                    badge="실시간",
                ),
                secondary_action=ScreenActionResponse(
                    key="open_home",
                    label="홈으로 이동",
                    route="/home",
                    style="ghost",
                    badge=None,
                ),
            ),
            device_name="LG ThinQ Washer",
            connection_status="연결됨",
            status_image_key="device_connected",
            last_synced_at=progress.generated_at,
            highlights=[
                f"현재 상태: {progress.current_status}",
                f"적재율: {progress.sensor_summary.load_ratio}%",
                f"예상 종료: {progress.expected_end_time}",
            ],
            cards=[
                DeviceInfoCardResponse(
                    key="load",
                    title="현재 적재량",
                    icon_key="load",
                    value=f"{progress.sensor_summary.current_load_kg:.1f}kg / {progress.sensor_summary.washer_capacity_kg:.1f}kg",
                    summary=f"적재율 {progress.sensor_summary.load_ratio}%",
                    route="/wash/progress",
                ),
                DeviceInfoCardResponse(
                    key="status",
                    title="현재 상태",
                    icon_key="status",
                    value=progress.current_status,
                    summary=progress.update_reason,
                    route="/wash/progress",
                ),
                DeviceInfoCardResponse(
                    key="finish",
                    title="예상 종료",
                    icon_key="finish",
                    value=progress.expected_end_time,
                    summary=f"남은 시간 {progress.remaining_time}분",
                    route="/wash/progress",
                ),
            ],
            actions=[
                ScreenActionResponse(
                    key="progress",
                    label="세탁 진행 보기",
                    route="/wash/progress",
                    style="primary",
                    badge="실시간",
                ),
                ScreenActionResponse(
                    key="timing",
                    label="세탁 타이밍 보기",
                    route="/wash/timing",
                    style="secondary",
                    badge=None,
                ),
            ],
        )
