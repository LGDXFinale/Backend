from __future__ import annotations

from typing import get_args

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.drying_optimization.schemas import DryRecommendationResponse
from app.drying_optimization.service import get_dry_recommendation
from app.home.schemas import (
    HomeNavigationItemResponse,
    HomeSummaryCardResponse,
    HomeSummaryResponse,
)
from app.laundry_progress.schemas import ContaminationLevel, LaundryProgressResponse
from app.laundry_progress.service import get_laundry_progress_status
from app.laundry_timing.schemas import LaundryRecommendationResponse
from app.laundry_timing.service import LaundryTimingService


DEFAULT_CONTA_LEVEL = get_args(ContaminationLevel)[1]


class HomeSummaryService:
    def __init__(self) -> None:
        self.timing_service = LaundryTimingService()

    async def build_home_summary(
        self,
        *,
        scenario: str = DEFAULT_DEMO_SCENARIO,
        member_id: str | None = None,
        washer_id: str | None = None,
        region: str | None = None,
        address: str | None = None,
        address_type: str = "auto",
        nx: int | None = None,
        ny: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        mid_land_reg_id: str | None = None,
        mid_ta_reg_id: str | None = None,
        current_load_kg: float | None = None,
        washer_capacity_kg: float | None = None,
        load_variation_kg: float | None = None,
        cycle_elapsed_minutes: int | None = None,
        base_cycle_minutes: int | None = None,
        final_spin_rpm: int | None = None,
    ) -> HomeSummaryResponse:
        defaults = get_demo_scenario(scenario)
        resolved_member_id = member_id or defaults.member_id
        resolved_washer_id = washer_id or defaults.washer_id
        resolved_region = region or defaults.region
        resolved_current_load_kg = (
            current_load_kg if current_load_kg is not None else defaults.current_load_kg
        )
        resolved_washer_capacity_kg = (
            washer_capacity_kg
            if washer_capacity_kg is not None
            else defaults.washer_capacity_kg
        )
        resolved_load_variation_kg = (
            load_variation_kg
            if load_variation_kg is not None
            else defaults.load_variation_kg
        )
        resolved_cycle_elapsed_minutes = (
            cycle_elapsed_minutes
            if cycle_elapsed_minutes is not None
            else defaults.cycle_elapsed_minutes
        )
        resolved_base_cycle_minutes = (
            base_cycle_minutes
            if base_cycle_minutes is not None
            else defaults.base_cycle_minutes
        )
        resolved_final_spin_rpm = (
            final_spin_rpm if final_spin_rpm is not None else defaults.final_spin_rpm
        )

        progress = get_laundry_progress_status(
            member_id=resolved_member_id,
            wash_status_id=defaults.wash_status_id,
            washer_id=resolved_washer_id,
            conta_level=DEFAULT_CONTA_LEVEL,
            wash_status=1,
            current_load_kg=resolved_current_load_kg,
            washer_capacity_kg=resolved_washer_capacity_kg,
            load_variation_kg=resolved_load_variation_kg,
            contamination_sensor_percent=None,
            cycle_elapsed_minutes=resolved_cycle_elapsed_minutes,
            base_cycle_minutes=resolved_base_cycle_minutes,
            final_spin_rpm=resolved_final_spin_rpm,
        )

        timing = await self.timing_service.build_laundry_recommendation(
            member_id=resolved_member_id,
            washer_id=resolved_washer_id,
            current_weight=resolved_current_load_kg,
            washer_capacity=resolved_washer_capacity_kg,
            hours_since_last_wash=defaults.hours_since_last_wash,
            weight_increase=defaults.weight_increase_kg,
            household_size=defaults.household_size,
            urgent_clothing_count=defaults.urgent_clothing_count,
            basket_sensor_weight_kg=resolved_current_load_kg,
            manual_refresh=False,
            forecast_hours=48,
            region=resolved_region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
        )

        drying = await get_dry_recommendation(
            member_id=resolved_member_id,
            washer_id=resolved_washer_id,
            region=resolved_region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
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
            final_spin_rpm=resolved_final_spin_rpm,
            pre_spin_weight_kg=None,
            post_spin_weight_kg=None,
        )

        timing_card = self._build_timing_card(timing)
        progress_card = self._build_progress_card(progress)
        drying_card = self._build_drying_card(drying)

        return HomeSummaryResponse(
            generated_at=timing.generated_at,
            member_id=resolved_member_id,
            washer_id=resolved_washer_id,
            location_label=drying.weather_info.location_label,
            timing=timing_card,
            progress=progress_card,
            drying=drying_card,
            shortcuts=self._build_shortcuts(),
            tabs=self._build_tabs(),
            cards=[timing_card, progress_card, drying_card],
        )

    def _build_timing_card(
        self, recommendation: LaundryRecommendationResponse
    ) -> HomeSummaryCardResponse:
        return HomeSummaryCardResponse(
            key="timing",
            title="세탁 타이밍 추천",
            headline=recommendation.recommendation,
            summary=recommendation.reason,
            level=recommendation.recommend_level,
            badge=self._level_label(recommendation.recommend_level),
            status_image_key=recommendation.status_image_key,
            updated_at=recommendation.generated_at,
            primary_value=recommendation.execution_window,
            secondary_value=recommendation.weather_summary,
            route="/wash/timing",
            action_items=recommendation.action_items[:2],
        )

    def _build_progress_card(
        self, progress: LaundryProgressResponse
    ) -> HomeSummaryCardResponse:
        return HomeSummaryCardResponse(
            key="progress",
            title="세탁 진행 상황",
            headline=progress.current_status,
            summary=progress.update_reason,
            level=self._progress_level(progress.progress_percent),
            badge=f"{progress.progress_percent}%",
            status_image_key=progress.status_image_key,
            updated_at=progress.generated_at,
            primary_value=f"{progress.remaining_time}분 남음",
            secondary_value=progress.expected_end_time,
            route="/wash/progress",
            action_items=progress.stage_notes[:2],
        )

    def _build_drying_card(
        self, recommendation: DryRecommendationResponse
    ) -> HomeSummaryCardResponse:
        return HomeSummaryCardResponse(
            key="drying",
            title="건조 추천",
            headline=recommendation.recommendation,
            summary=recommendation.reason,
            level=recommendation.recommend_level,
            badge=recommendation.recommend_level_label,
            status_image_key=recommendation.status_image_key,
            updated_at=recommendation.generated_at,
            primary_value=recommendation.dry_rec_method_name,
            secondary_value=recommendation.weather_info.weather_summary,
            route="/dry/recommend",
            action_items=recommendation.action_items[:2],
        )

    def _progress_level(self, progress_percent: int) -> str:
        if progress_percent >= 80:
            return "high"
        if progress_percent >= 40:
            return "medium"
        return "low"

    def _level_label(self, level: str) -> str:
        mapping = {
            "high": "높음",
            "medium": "보통",
            "low": "낮음",
        }
        return mapping.get(level, level)

    def _build_shortcuts(self) -> list[HomeNavigationItemResponse]:
        return [
            HomeNavigationItemResponse(
                key="timing",
                label="세탁 타이밍",
                route="/wash/timing",
                icon_key="wash_timing",
                badge="추천",
            ),
            HomeNavigationItemResponse(
                key="progress",
                label="세탁 진행",
                route="/wash/progress",
                icon_key="wash_progress",
                badge="실시간",
            ),
            HomeNavigationItemResponse(
                key="drying",
                label="건조 추천",
                route="/dry/recommend",
                icon_key="dry_recommend",
                badge=None,
            ),
        ]

    def _build_tabs(self) -> list[HomeNavigationItemResponse]:
        return [
            HomeNavigationItemResponse(
                key="home",
                label="홈",
                route="/home",
                icon_key="home",
                badge=None,
            ),
            HomeNavigationItemResponse(
                key="device",
                label="디바이스",
                route="/device",
                icon_key="device",
                badge=None,
            ),
            HomeNavigationItemResponse(
                key="care",
                label="케어",
                route="/care",
                icon_key="care",
                badge=None,
            ),
            HomeNavigationItemResponse(
                key="menu",
                label="메뉴",
                route="/menu",
                icon_key="menu",
                badge=None,
            ),
        ]
