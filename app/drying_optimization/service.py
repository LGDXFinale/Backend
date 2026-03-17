from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import requests

from app.drying_optimization.schemas import (
    DryRecommendationResponse,
    DryWeatherInfoResponse,
    DryingConsiderationResponse,
)


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

METHOD_MAP = {
    1: "실내건조",
    2: "실외건조",
    3: "건조기",
}


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
        city: str,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
        humidity_override: int | None,
        temperature_override: float | None,
        is_raining_override: bool | None,
    ) -> DryRecommendationResponse:
        self._validate_inputs(
            city=city,
            laundry_weight_kg=laundry_weight_kg,
            humidity_override=humidity_override,
        )

        weather = self._get_weather_snapshot(
            city=city,
            humidity_override=humidity_override,
            temperature_override=temperature_override,
            is_raining_override=is_raining_override,
        )
        drying_score = self._calculate_drying_score(
            weather=weather,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
        )
        decision = self._build_decision(
            weather=weather,
            drying_score=drying_score,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
        )
        considerations = self._build_considerations(
            weather=weather,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
        )
        action_items = self._build_action_items(
            decision=decision,
            weather=weather,
            has_delicate_items=has_delicate_items,
            has_outdoor_space=has_outdoor_space,
        )

        return DryRecommendationResponse(
            generated_at=datetime.now().isoformat(timespec="seconds"),
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
        if (
            humidity_override is not None
            or temperature_override is not None
            or is_raining_override is not None
        ):
            humidity = humidity_override if humidity_override is not None else 55
            temperature = temperature_override if temperature_override is not None else 22.0
            is_raining = is_raining_override if is_raining_override is not None else False
            return WeatherSnapshot(
                source="manual_override",
                city=city,
                weather_main="Override",
                weather_description="manual input",
                is_raining=is_raining,
                humidity=humidity,
                temperature=temperature,
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

        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
        }

        try:
            response = requests.get(OPENWEATHER_URL, params=params, timeout=5)
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
        weather_description = data.get("weather", [{}])[0].get("description")
        humidity = int(data.get("main", {}).get("humidity", 55))
        temperature = float(data.get("main", {}).get("temp", 22.0))
        wind_speed = data.get("wind", {}).get("speed")
        is_raining = weather_main in {"Rain", "Drizzle", "Thunderstorm", "Snow"}

        return WeatherSnapshot(
            source="openweather",
            city=city,
            weather_main=weather_main,
            weather_description=weather_description,
            is_raining=is_raining,
            humidity=humidity,
            temperature=temperature,
            wind_speed_mps=float(wind_speed) if wind_speed is not None else None,
            weather_error=None,
        )

    def _calculate_drying_score(
        self,
        *,
        weather: WeatherSnapshot,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
    ) -> int:
        dryer_score = 15

        if weather.is_raining:
            dryer_score += 35
        if weather.humidity >= 80:
            dryer_score += 25
        elif weather.humidity >= 65:
            dryer_score += 10

        if weather.temperature < 10:
            dryer_score += 15
        elif weather.temperature < 18:
            dryer_score += 8

        if laundry_weight_kg >= 5:
            dryer_score += 10
        elif laundry_weight_kg >= 3:
            dryer_score += 5

        if needs_fast_dry:
            dryer_score += 20
        if not has_outdoor_space:
            dryer_score += 12
        if has_delicate_items:
            dryer_score -= 15

        return max(0, min(dryer_score, 100))

    def _build_decision(
        self,
        *,
        weather: WeatherSnapshot,
        drying_score: int,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
    ) -> DryDecision:
        if has_delicate_items and not needs_fast_dry:
            if weather.is_raining or weather.humidity >= 70 or not has_outdoor_space:
                return DryDecision(
                    method=1,
                    time_minutes=240,
                    recommendation="실내건조 추천",
                    reason="민감한 소재가 있어 강한 열 건조보다 실내의 완만한 건조가 안전합니다.",
                    recommend_level="medium",
                    status_image_key="indoor_safe",
                    caution="두꺼운 의류와 겹치지 않게 간격을 두고 널어주세요.",
                    energy_tip="제습기나 선풍기를 함께 사용하면 실내건조 시간을 줄일 수 있습니다.",
                )

        if weather.is_raining or drying_score >= 70:
            return DryDecision(
                method=3,
                time_minutes=70 if weather.humidity >= 80 else 60,
                recommendation="건조기 추천",
                reason="비나 높은 습도로 자연 건조 효율이 낮아 건조기가 가장 안정적입니다.",
                recommend_level="high",
                status_image_key="dryer_recommended",
                caution="민감 소재가 있다면 저온 코스 또는 건조망 사용을 고려하세요.",
                energy_tip="탈수를 충분히 한 뒤 건조기에 넣으면 시간을 줄일 수 있습니다.",
            )

        if has_outdoor_space and weather.humidity < 60 and weather.temperature >= 20 and not weather.is_raining:
            return DryDecision(
                method=2,
                time_minutes=120 if laundry_weight_kg < 4 else 150,
                recommendation="실외건조 추천",
                reason="기온과 습도가 양호해 자연 건조 효율이 좋습니다.",
                recommend_level="low",
                status_image_key="outdoor_recommended",
                caution="직사광선이 강하면 색 바램이 생길 수 있어 뒤집어 널어주세요.",
                energy_tip="바람이 잘 통하는 오전이나 낮 시간대를 활용하면 더 빠르게 마릅니다.",
            )

        return DryDecision(
            method=1,
            time_minutes=180 if laundry_weight_kg < 4 else 220,
            recommendation="실내건조 추천",
            reason="현재 조건에서는 실내에서 통풍을 확보해 건조하는 방식이 가장 무난합니다.",
            recommend_level="medium",
            status_image_key="indoor_recommended",
            caution="습도가 높다면 밀폐된 공간보다 창가나 환기 가능한 공간이 좋습니다.",
            energy_tip="선풍기 방향을 빨랫감 측면으로 두면 건조 시간을 줄일 수 있습니다.",
        )

    def _build_considerations(
        self,
        *,
        weather: WeatherSnapshot,
        laundry_weight_kg: float,
        has_delicate_items: bool,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
    ) -> list[DryingConsiderationResponse]:
        considerations = [
            DryingConsiderationResponse(
                category="외부 날씨",
                score=self._weather_score(weather),
                summary=self._weather_summary(weather),
                details=[
                    f"현재 습도는 {weather.humidity}%입니다.",
                    f"현재 기온은 {weather.temperature:.1f}도입니다.",
                    f"강수 여부는 {'비 또는 눈 예상' if weather.is_raining else '뚜렷한 강수 없음'}입니다.",
                ],
            ),
            DryingConsiderationResponse(
                category="세탁물 양",
                score=min(100, round(laundry_weight_kg * 18)),
                summary=self._load_summary(laundry_weight_kg),
                details=[
                    f"현재 건조 대상 세탁물 무게는 {laundry_weight_kg:.1f}kg입니다.",
                    "세탁물 양이 많을수록 자연 건조 시간 편차가 커집니다.",
                ],
            ),
            DryingConsiderationResponse(
                category="민감 소재",
                score=75 if has_delicate_items else 20,
                summary=(
                    "민감한 소재가 있어 강한 열을 피하는 편이 좋습니다."
                    if has_delicate_items
                    else "고온 건조에 특별히 취약한 요소는 크지 않습니다."
                ),
                details=[
                    "실크, 울, 기능성 의류, 프린트 의류는 건조 방식 선택에 영향을 줍니다.",
                    f"민감 소재 포함 여부: {'예' if has_delicate_items else '아니오'}",
                ],
            ),
            DryingConsiderationResponse(
                category="사용자 조건",
                score=self._user_condition_score(
                    needs_fast_dry=needs_fast_dry,
                    has_outdoor_space=has_outdoor_space,
                ),
                summary=self._user_condition_summary(
                    needs_fast_dry=needs_fast_dry,
                    has_outdoor_space=has_outdoor_space,
                ),
                details=[
                    f"빠른 건조 필요 여부: {'예' if needs_fast_dry else '아니오'}",
                    f"실외 건조 가능 여부: {'예' if has_outdoor_space else '아니오'}",
                ],
            ),
        ]

        return sorted(considerations, key=lambda item: item.score, reverse=True)[:3]

    def _build_action_items(
        self,
        *,
        decision: DryDecision,
        weather: WeatherSnapshot,
        has_delicate_items: bool,
        has_outdoor_space: bool,
    ) -> list[str]:
        actions: list[str] = []

        if decision.method == 3:
            actions.append("건조기 사용 전 세탁물을 한 번 털어주면 주름과 뭉침을 줄일 수 있습니다.")
        elif decision.method == 2:
            actions.append("바람이 잘 통하는 위치에 간격을 두고 널어주면 실외건조 효율이 좋아집니다.")
        else:
            actions.append("실내건조 시 창문 환기나 보조 송풍을 함께 사용하면 건조 시간이 단축됩니다.")

        if has_delicate_items:
            actions.append("민감 소재는 뒤집어서 널거나 저온 코스를 우선 검토하세요.")

        if weather.humidity >= 75 and decision.method != 3:
            actions.append("습도가 높으니 제습기나 선풍기 보조를 함께 쓰는 편이 좋습니다.")

        if not has_outdoor_space:
            actions.append("실외 공간이 없다면 빨랫감 간격을 평소보다 넓게 두는 것이 중요합니다.")

        if not actions:
            actions.append("현재 조건에 맞는 기본 건조 방식으로 진행하면 됩니다.")

        return actions

    def _validate_inputs(
        self,
        *,
        city: str,
        laundry_weight_kg: float,
        humidity_override: int | None,
    ) -> None:
        if not city.strip():
            raise ValueError("city는 비어 있을 수 없습니다.")
        if laundry_weight_kg <= 0:
            raise ValueError("laundry_weight_kg는 0보다 커야 합니다.")
        if humidity_override is not None and not 0 <= humidity_override <= 100:
            raise ValueError("humidity_override는 0 이상 100 이하여야 합니다.")

    def _weather_score(self, weather: WeatherSnapshot) -> int:
        score = 10
        if weather.is_raining:
            score += 45
        if weather.humidity >= 80:
            score += 30
        elif weather.humidity >= 65:
            score += 15
        if weather.temperature < 10:
            score += 15
        return min(score, 100)

    def _weather_summary(self, weather: WeatherSnapshot) -> str:
        if weather.is_raining and weather.humidity >= 80:
            return "비와 높은 습도로 자연 건조 효율이 매우 낮습니다."
        if weather.is_raining:
            return "비가 있어 자연 건조보다 실내 또는 건조기 쪽이 안정적입니다."
        if weather.humidity >= 80:
            return "습도가 매우 높아 건조 시간이 길어질 가능성이 큽니다."
        if weather.humidity < 60 and weather.temperature >= 20:
            return "건조하기에 비교적 무난한 날씨입니다."
        return "건조 여건이 아주 나쁘진 않지만 빠른 자연 건조를 기대하긴 어렵습니다."

    def _load_summary(self, laundry_weight_kg: float) -> str:
        if laundry_weight_kg >= 5:
            return "세탁물 양이 많아 건조 방식 선택의 영향이 큽니다."
        if laundry_weight_kg >= 3:
            return "중간 이상 분량이라 건조 시간이 다소 길 수 있습니다."
        return "세탁물 양이 적어 선택 폭이 비교적 넓습니다."

    def _user_condition_score(
        self,
        *,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
    ) -> int:
        score = 20
        if needs_fast_dry:
            score += 45
        if not has_outdoor_space:
            score += 25
        return min(score, 100)

    def _user_condition_summary(
        self,
        *,
        needs_fast_dry: bool,
        has_outdoor_space: bool,
    ) -> str:
        if needs_fast_dry and not has_outdoor_space:
            return "빠른 건조가 필요하고 실외 공간이 없어 기계 건조 선호도가 높습니다."
        if needs_fast_dry:
            return "빠른 건조가 필요해 자연 건조보다 즉시성이 중요합니다."
        if not has_outdoor_space:
            return "실외 건조 공간이 없어 실내 또는 건조기 중심으로 판단해야 합니다."
        return "사용자 조건상 건조 방식 선택에 큰 제약은 없습니다."


def get_dry_recommendation(
    *,
    city: str = "Seoul",
    laundry_weight_kg: float = 3.0,
    has_delicate_items: bool = False,
    needs_fast_dry: bool = False,
    has_outdoor_space: bool = True,
    humidity_override: int | None = None,
    temperature_override: float | None = None,
    is_raining_override: bool | None = None,
) -> DryRecommendationResponse:
    service = DryingOptimizationService()
    return service.build_recommendation(
        city=city,
        laundry_weight_kg=laundry_weight_kg,
        has_delicate_items=has_delicate_items,
        needs_fast_dry=needs_fast_dry,
        has_outdoor_space=has_outdoor_space,
        humidity_override=humidity_override,
        temperature_override=temperature_override,
        is_raining_override=is_raining_override,
    )
