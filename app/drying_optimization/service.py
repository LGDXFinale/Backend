from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import requests

from app.demo_defaults import (
    DEMO_AIRFLOW_LEVEL,
    DEMO_CITY,
    DEMO_DEHUMIDIFIER_ON,
    DEMO_DRY_LAUNDRY_WEIGHT_KG,
    DEMO_FINAL_SPIN_RPM,
    DEMO_HAS_DELICATE_ITEMS,
    DEMO_HAS_DRYER,
    DEMO_HAS_OUTDOOR_SPACE,
    DEMO_INDOOR_HUMIDITY,
    DEMO_INDOOR_TEMPERATURE,
    DEMO_MEMBER_ID,
    DEMO_NEEDS_FAST_DRY,
    DEMO_ODOR_SENSITIVE,
    DEMO_WASHER_ID,
)
from app.drying_optimization.schemas import (
    DryEnvironmentAnalysisResponse,
    DryRecommendationResponse,
    DryWeatherInfoResponse,
    DryingConsiderationResponse,
    IndoorEnvironmentResponse,
    MoistureEstimationResponse,
)


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
METHOD_MAP = {1: "실내건조", 2: "자연건조", 3: "건조기", 4: "혼합건조"}


@dataclass(frozen=True)
class WeatherSnapshot:
    source: str
    city: str
    weather_main: str | None
    weather_description: str | None
    is_raining: bool
    humidity: int
    temperature: float
    wind_speed_mps: float | None
    weather_error: str | None


@dataclass(frozen=True)
class IndoorEnvironment:
    humidity: int
    temperature: float
    airflow_level: int
    dehumidifier_on: bool


@dataclass(frozen=True)
class MoistureEstimation:
    estimated_moisture_percent: int
    residual_water_kg: float
    weight_change_kg: float | None
    final_spin_rpm: int
    odor_risk_level: str


@dataclass(frozen=True)
class EnvironmentAnalysis:
    indoor_score: int
    outdoor_score: int
    preferred_environment: str
    summary: str


@dataclass(frozen=True)
class DryDecision:
    method: int
    time_minutes: int
    recommendation: str
    reason: str
    recommend_level: str
    status_image_key: str
    caution: str
    energy_tip: str


class DryingOptimizationService:
    def build_recommendation(
        self,
        *,
        member_id: str,
        washer_id: str,
        city: str,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
        has_dryer: bool,
        odor_sensitive: bool,
        indoor_humidity: int,
        indoor_temperature: float,
        airflow_level: int,
        dehumidifier_on: bool,
        final_spin_rpm: int,
        pre_spin_weight_kg: float | None,
        post_spin_weight_kg: float | None,
        humidity_override: int | None,
        temperature_override: float | None,
        is_raining_override: bool | None,
    ) -> DryRecommendationResponse:
        self._validate_inputs(
            city=city,
            laundry_weight_kg=laundry_weight_kg,
            indoor_humidity=indoor_humidity,
            airflow_level=airflow_level,
            final_spin_rpm=final_spin_rpm,
            pre_spin_weight_kg=pre_spin_weight_kg,
            post_spin_weight_kg=post_spin_weight_kg,
            humidity_override=humidity_override,
        )

        weather = self._get_weather_snapshot(
            city=city,
            humidity_override=humidity_override,
            temperature_override=temperature_override,
            is_raining_override=is_raining_override,
        )
        indoor = IndoorEnvironment(
            humidity=indoor_humidity,
            temperature=indoor_temperature,
            airflow_level=airflow_level,
            dehumidifier_on=dehumidifier_on,
        )
        moisture = self._estimate_moisture(
            laundry_weight_kg=laundry_weight_kg,
            final_spin_rpm=final_spin_rpm,
            pre_spin_weight_kg=pre_spin_weight_kg,
            post_spin_weight_kg=post_spin_weight_kg,
            weather=weather,
            indoor=indoor,
            odor_sensitive=odor_sensitive,
        )
        environment = self._analyze_environment(
            weather=weather,
            indoor=indoor,
            has_outdoor_space=has_outdoor_space,
        )
        decision = self._build_decision(
            weather=weather,
            indoor=indoor,
            moisture=moisture,
            environment=environment,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
            has_dryer=has_dryer,
        )
        considerations = self._build_considerations(
            weather=weather,
            indoor=indoor,
            moisture=moisture,
            environment=environment,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
        )
        action_items = self._build_action_items(
            decision=decision,
            indoor=indoor,
            moisture=moisture,
            has_delicate_items=has_delicate_items,
            has_dryer=has_dryer,
        )

        return DryRecommendationResponse(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            member_id=member_id,
            washer_id=washer_id,
            dry_rec_id="DR001",
            dry_rec_time=decision.time_minutes,
            dry_rec_method=decision.method,
            dry_rec_method_name=METHOD_MAP[decision.method],
            recommendation=decision.recommendation,
            reason=decision.reason,
            recommend_level=decision.recommend_level,  # type: ignore[arg-type]
            status_image_key=decision.status_image_key,
            caution=decision.caution,
            energy_tip=decision.energy_tip,
            weather_info=DryWeatherInfoResponse(
                source=weather.source,
                city=weather.city,
                weather_main=weather.weather_main,
                weather_description=weather.weather_description,
                is_raining=weather.is_raining,
                humidity=weather.humidity,
                temperature=weather.temperature,
                wind_speed_mps=weather.wind_speed_mps,
                weather_error=weather.weather_error,
            ),
            indoor_environment=IndoorEnvironmentResponse(
                indoor_humidity=indoor.humidity,
                indoor_temperature=indoor.temperature,
                airflow_level=indoor.airflow_level,
                dehumidifier_on=indoor.dehumidifier_on,
            ),
            moisture_estimation=MoistureEstimationResponse(
                estimated_moisture_percent=moisture.estimated_moisture_percent,
                residual_water_kg=moisture.residual_water_kg,
                weight_change_kg=moisture.weight_change_kg,
                final_spin_rpm=moisture.final_spin_rpm,
                odor_risk_level=moisture.odor_risk_level,  # type: ignore[arg-type]
            ),
            environment_analysis=DryEnvironmentAnalysisResponse(
                indoor_score=environment.indoor_score,
                outdoor_score=environment.outdoor_score,
                preferred_environment=environment.preferred_environment,
                summary=environment.summary,
            ),
            top_considerations=considerations,
            action_items=action_items,
        )

    def _get_weather_snapshot(
        self,
        *,
        city: str,
        humidity_override: int | None,
        temperature_override: float | None,
        is_raining_override: bool | None,
    ) -> WeatherSnapshot:
        if humidity_override is not None or temperature_override is not None or is_raining_override is not None:
            return WeatherSnapshot(
                source="manual_override",
                city=city,
                weather_main="Override",
                weather_description="manual input",
                is_raining=is_raining_override if is_raining_override is not None else False,
                humidity=humidity_override if humidity_override is not None else 55,
                temperature=temperature_override if temperature_override is not None else 22.0,
                wind_speed_mps=None,
                weather_error=None,
            )

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return WeatherSnapshot(
                source="fallback",
                city=city,
                weather_main="Clear",
                weather_description="default fallback",
                is_raining=False,
                humidity=55,
                temperature=22.0,
                wind_speed_mps=1.5,
                weather_error="OPENWEATHER_API_KEY 값을 찾을 수 없어 기본 날씨를 사용했습니다.",
            )

        try:
            response = requests.get(
                OPENWEATHER_URL,
                params={"q": city, "appid": api_key, "units": "metric"},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return WeatherSnapshot(
                source="fallback",
                city=city,
                weather_main="Clouds",
                weather_description="network fallback",
                is_raining=False,
                humidity=60,
                temperature=21.0,
                wind_speed_mps=None,
                weather_error=f"외부 날씨 API 호출에 실패해 기본 날씨를 사용했습니다: {exc}",
            )

        weather_main = data.get("weather", [{}])[0].get("main")
        return WeatherSnapshot(
            source="openweather",
            city=city,
            weather_main=weather_main,
            weather_description=data.get("weather", [{}])[0].get("description"),
            is_raining=weather_main in {"Rain", "Drizzle", "Thunderstorm", "Snow"},
            humidity=int(data.get("main", {}).get("humidity", 55)),
            temperature=float(data.get("main", {}).get("temp", 22.0)),
            wind_speed_mps=(
                float(data.get("wind", {}).get("speed")) if data.get("wind", {}).get("speed") is not None else None
            ),
            weather_error=None,
        )

    def _estimate_moisture(
        self,
        *,
        laundry_weight_kg: float,
        final_spin_rpm: int,
        pre_spin_weight_kg: float | None,
        post_spin_weight_kg: float | None,
        weather: WeatherSnapshot,
        indoor: IndoorEnvironment,
        odor_sensitive: bool,
    ) -> MoistureEstimation:
        weight_change_kg = None
        if pre_spin_weight_kg is not None and post_spin_weight_kg is not None:
            weight_change_kg = round(max(pre_spin_weight_kg - post_spin_weight_kg, 0), 2)

        rpm_factor = 0.16 if final_spin_rpm >= 1200 else 0.22 if final_spin_rpm >= 900 else 0.3
        base_residual = laundry_weight_kg * rpm_factor
        if weight_change_kg is not None:
            base_residual = max(base_residual, (pre_spin_weight_kg or 0) - (post_spin_weight_kg or 0))
            base_residual = max(0.2, round(base_residual * 0.4, 2))
        residual_water_kg = round(base_residual, 2)

        moisture_percent = round(min((residual_water_kg / max(laundry_weight_kg, 0.1)) * 100, 100))
        odor_score = 0
        if moisture_percent >= 30:
            odor_score += 45
        elif moisture_percent >= 20:
            odor_score += 25
        if indoor.humidity >= 70 or weather.humidity >= 75:
            odor_score += 25
        if odor_sensitive:
            odor_score += 10
        odor_risk_level = "high" if odor_score >= 60 else "medium" if odor_score >= 30 else "low"

        return MoistureEstimation(
            estimated_moisture_percent=moisture_percent,
            residual_water_kg=residual_water_kg,
            weight_change_kg=weight_change_kg,
            final_spin_rpm=final_spin_rpm,
            odor_risk_level=odor_risk_level,
        )

    def _analyze_environment(
        self,
        *,
        weather: WeatherSnapshot,
        indoor: IndoorEnvironment,
        has_outdoor_space: bool,
    ) -> EnvironmentAnalysis:
        indoor_score = 55 + indoor.airflow_level // 3
        indoor_score -= max(indoor.humidity - 60, 0) // 2
        indoor_score += 12 if indoor.dehumidifier_on else 0

        outdoor_score = 60
        outdoor_score -= 30 if weather.is_raining else 0
        outdoor_score -= max(weather.humidity - 60, 0) // 2
        outdoor_score += 10 if weather.temperature >= 20 else 0
        outdoor_score += 8 if (weather.wind_speed_mps or 0) >= 2 else 0
        if not has_outdoor_space:
            outdoor_score = 0

        indoor_score = max(0, min(indoor_score, 100))
        outdoor_score = max(0, min(outdoor_score, 100))

        if indoor_score >= outdoor_score + 10:
            preferred_environment = "indoor"
            summary = "실내 환경이 더 안정적이어서 실내 중심 건조가 유리합니다."
        elif outdoor_score >= indoor_score + 10:
            preferred_environment = "outdoor"
            summary = "실외 자연 건조 조건이 상대적으로 더 좋습니다."
        else:
            preferred_environment = "mixed"
            summary = "실내외 장단점이 비슷해 혼합 건조 전략이 효율적입니다."

        return EnvironmentAnalysis(
            indoor_score=indoor_score,
            outdoor_score=outdoor_score,
            preferred_environment=preferred_environment,
            summary=summary,
        )

    def _build_decision(
        self,
        *,
        weather: WeatherSnapshot,
        indoor: IndoorEnvironment,
        moisture: MoistureEstimation,
        environment: EnvironmentAnalysis,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
        has_dryer: bool,
    ) -> DryDecision:
        if has_delicate_items and moisture.estimated_moisture_percent >= 20 and has_dryer and needs_fast_dry:
            return DryDecision(
                method=4,
                time_minutes=150,
                recommendation="혼합건조 추천",
                reason="민감 소재 보호와 빠른 건조를 함께 맞추려면 짧은 저온 건조 후 자연 건조가 효율적입니다.",
                recommend_level="high",
                status_image_key="mixed_recommended",
                caution="민감 소재는 고온 장시간 건조를 피하고 마무리 자연 건조를 권장합니다.",
                energy_tip="탈수 후 20~30분 저온 건조만 사용하면 전체 시간을 줄일 수 있습니다.",
            )

        if has_dryer and (weather.is_raining or moisture.odor_risk_level == "high" or needs_fast_dry):
            return DryDecision(
                method=3,
                time_minutes=70 if moisture.estimated_moisture_percent >= 25 else 55,
                recommendation="건조기 추천",
                reason="수분도 또는 냄새 위험이 높아 건조기가 가장 안정적인 선택입니다.",
                recommend_level="high",
                status_image_key="dryer_recommended",
                caution="민감 소재가 있으면 저온 코스 사용을 우선 검토하세요.",
                energy_tip="탈수를 충분히 한 뒤 건조기에 넣으면 에너지 사용량을 줄일 수 있습니다.",
            )

        if environment.preferred_environment == "outdoor" and has_outdoor_space and not has_delicate_items:
            return DryDecision(
                method=2,
                time_minutes=120 if moisture.estimated_moisture_percent < 25 else 150,
                recommendation="자연건조 추천",
                reason="실외 환경이 건조에 유리하고 민감 소재 부담도 크지 않습니다.",
                recommend_level="low",
                status_image_key="outdoor_recommended",
                caution="직사광선이 강하면 색 바램이 생길 수 있어 뒤집어서 널어주세요.",
                energy_tip="바람이 잘 통하는 시간대를 활용하면 건조 시간을 줄일 수 있습니다.",
            )

        if environment.preferred_environment == "mixed" and has_outdoor_space:
            return DryDecision(
                method=4,
                time_minutes=170,
                recommendation="혼합건조 추천",
                reason="실내외 환경 점수가 비슷해 초기 실내 건조 후 자연 건조로 전환하는 방식이 효율적입니다.",
                recommend_level="medium",
                status_image_key="mixed_recommended",
                caution="중간에 한 번 뒤집어 널면 잔수분 편차를 줄일 수 있습니다.",
                energy_tip="실내 송풍을 먼저 사용한 뒤 자연 건조로 전환하면 전체 시간이 단축됩니다.",
            )

        return DryDecision(
            method=1,
            time_minutes=180 if moisture.estimated_moisture_percent < 25 else 220,
            recommendation="실내건조 추천",
            reason="현재 조건에서는 실내 통풍을 확보한 건조가 가장 무난합니다.",
            recommend_level="medium",
            status_image_key="indoor_recommended",
            caution="실내 습도가 높다면 빨랫감 간격을 넓게 유지하세요.",
            energy_tip="선풍기나 제습기를 함께 쓰면 실내건조 시간을 줄일 수 있습니다.",
        )

    def _build_considerations(
        self,
        *,
        weather: WeatherSnapshot,
        indoor: IndoorEnvironment,
        moisture: MoistureEstimation,
        environment: EnvironmentAnalysis,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
    ) -> list[DryingConsiderationResponse]:
        considerations = [
            DryingConsiderationResponse(
                category="수분도",
                score=min(100, moisture.estimated_moisture_percent * 2),
                summary=f"현재 추정 수분도는 {moisture.estimated_moisture_percent}%입니다.",
                details=[
                    f"잔여 수분 무게는 {moisture.residual_water_kg:.2f}kg입니다.",
                    f"탈수 RPM은 {moisture.final_spin_rpm}입니다.",
                    f"냄새 위험도는 {moisture.odor_risk_level}입니다.",
                ],
            ),
            DryingConsiderationResponse(
                category="실내외 환경 비교",
                score=max(environment.indoor_score, environment.outdoor_score),
                summary=environment.summary,
                details=[
                    f"실내 건조 적합도는 {environment.indoor_score}점입니다.",
                    f"실외 건조 적합도는 {environment.outdoor_score}점입니다.",
                    f"실외 날씨 습도는 {weather.humidity}%입니다.",
                ],
            ),
            DryingConsiderationResponse(
                category="세탁물 특성",
                score=70 if has_delicate_items else min(100, round(laundry_weight_kg * 18)),
                summary=(
                    "민감 소재가 있어 건조 방식 선택 시 열 손상 방지가 중요합니다."
                    if has_delicate_items
                    else "세탁물 양이 건조 시간과 방식 선택에 영향을 줍니다."
                ),
                details=[
                    f"세탁물 무게는 {laundry_weight_kg:.1f}kg입니다.",
                    f"민감 소재 포함 여부: {'예' if has_delicate_items else '아니오'}",
                    f"빠른 건조 필요 여부: {'예' if needs_fast_dry else '아니오'}",
                ],
            ),
        ]
        return sorted(considerations, key=lambda item: item.score, reverse=True)

    def _build_action_items(
        self,
        *,
        decision: DryDecision,
        indoor: IndoorEnvironment,
        moisture: MoistureEstimation,
        has_delicate_items: bool,
        has_dryer: bool,
    ) -> list[str]:
        actions: list[str] = []
        if decision.method == 3:
            actions.append("건조기 사용 전 빨랫감을 한 번 털어 넣으면 뭉침과 주름을 줄일 수 있습니다.")
        elif decision.method == 4:
            actions.append("초기 강제 건조 후 마무리 자연 건조로 전환하면 손상과 냄새를 함께 줄일 수 있습니다.")
        elif decision.method == 2:
            actions.append("바람이 잘 통하는 위치에 간격을 두고 널어 자연 건조 효율을 높이세요.")
        else:
            actions.append("실내건조 시 창문 환기나 보조 송풍을 함께 사용하면 건조 시간이 줄어듭니다.")

        if indoor.humidity >= 70 and decision.method != 3:
            actions.append("실내 습도가 높아 제습기나 추가 송풍 보조를 함께 쓰는 편이 좋습니다.")
        if has_delicate_items:
            actions.append("민감 소재는 뒤집거나 평건조를 우선 검토하세요.")
        if moisture.odor_risk_level == "high":
            actions.append("냄새 위험이 높아 건조 지연 없이 바로 널거나 건조를 시작하는 것이 좋습니다.")
        if not has_dryer and decision.method in {3, 4}:
            actions.append("건조기 미보유 환경이라면 제습기와 송풍을 함께 사용한 실내 중심 건조로 대체하세요.")
        return actions

    def _validate_inputs(
        self,
        *,
        city: str,
        laundry_weight_kg: float,
        indoor_humidity: int,
        airflow_level: int,
        final_spin_rpm: int,
        pre_spin_weight_kg: float | None,
        post_spin_weight_kg: float | None,
        humidity_override: int | None,
    ) -> None:
        if not city.strip():
            raise ValueError("city는 비어 있을 수 없습니다.")
        if laundry_weight_kg <= 0:
            raise ValueError("laundry_weight_kg는 0보다 커야 합니다.")
        if not 0 <= indoor_humidity <= 100:
            raise ValueError("indoor_humidity는 0 이상 100 이하여야 합니다.")
        if not 0 <= airflow_level <= 100:
            raise ValueError("airflow_level은 0 이상 100 이하여야 합니다.")
        if final_spin_rpm < 0:
            raise ValueError("final_spin_rpm은 음수일 수 없습니다.")
        if humidity_override is not None and not 0 <= humidity_override <= 100:
            raise ValueError("humidity_override는 0 이상 100 이하여야 합니다.")
        if (
            pre_spin_weight_kg is not None
            and post_spin_weight_kg is not None
            and pre_spin_weight_kg < post_spin_weight_kg
        ):
            raise ValueError("pre_spin_weight_kg는 post_spin_weight_kg보다 작을 수 없습니다.")


def get_dry_recommendation(
    *,
    member_id: str = DEMO_MEMBER_ID,
    washer_id: str = DEMO_WASHER_ID,
    city: str = DEMO_CITY,
    laundry_weight_kg: float = DEMO_DRY_LAUNDRY_WEIGHT_KG,
    has_delicate_items: bool = DEMO_HAS_DELICATE_ITEMS,
    needs_fast_dry: bool = DEMO_NEEDS_FAST_DRY,
    has_outdoor_space: bool = DEMO_HAS_OUTDOOR_SPACE,
    has_dryer: bool = DEMO_HAS_DRYER,
    odor_sensitive: bool = DEMO_ODOR_SENSITIVE,
    indoor_humidity: int = DEMO_INDOOR_HUMIDITY,
    indoor_temperature: float = DEMO_INDOOR_TEMPERATURE,
    airflow_level: int = DEMO_AIRFLOW_LEVEL,
    dehumidifier_on: bool = DEMO_DEHUMIDIFIER_ON,
    final_spin_rpm: int = DEMO_FINAL_SPIN_RPM,
    pre_spin_weight_kg: float | None = None,
    post_spin_weight_kg: float | None = None,
    humidity_override: int | None = None,
    temperature_override: float | None = None,
    is_raining_override: bool | None = None,
) -> DryRecommendationResponse:
    service = DryingOptimizationService()
    return service.build_recommendation(
        member_id=member_id,
        washer_id=washer_id,
        city=city,
        laundry_weight_kg=laundry_weight_kg,
        has_delicate_items=has_delicate_items,
        needs_fast_dry=needs_fast_dry,
        has_outdoor_space=has_outdoor_space,
        has_dryer=has_dryer,
        odor_sensitive=odor_sensitive,
        indoor_humidity=indoor_humidity,
        indoor_temperature=indoor_temperature,
        airflow_level=airflow_level,
        dehumidifier_on=dehumidifier_on,
        final_spin_rpm=final_spin_rpm,
        pre_spin_weight_kg=pre_spin_weight_kg,
        post_spin_weight_kg=post_spin_weight_kg,
        humidity_override=humidity_override,
        temperature_override=temperature_override,
        is_raining_override=is_raining_override,
    )
