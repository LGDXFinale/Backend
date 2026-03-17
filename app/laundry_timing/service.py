from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fastapi import HTTPException

from app.laundry_timing.schemas import (
    AirQualityResponse,
    LaundryRecommendationResponse,
    LaundryTimingConsiderationResponse,
    LaundryTimingWeatherSnapshotResponse,
    RegionPresetResponse,
    WeeklyWeatherResponse,
)
from app.utils import (
    AirQualityError,
    PublicDataWeatherError,
    VWorldGeocoderError,
    find_nearest_region_preset,
    geocode_address,
    get_current_air_quality,
    get_region_presets,
    get_weekly_weather,
    latlon_to_grid,
    resolve_region_preset,
)


AddressType = Literal["auto", "road", "parcel"]


@dataclass(frozen=True)
class ResolvedWeatherContext:
    location_label: str | None
    address_hint: str | None
    latitude: float | None
    longitude: float | None
    nx: int
    ny: int
    mid_land_reg_id: str
    mid_ta_reg_id: str


@dataclass(frozen=True)
class WeatherSignal:
    source: str
    location_label: str | None
    weather_error: str | None
    rain_expected: bool
    high_humidity: bool
    outdoor_drying_friendly: bool
    weather_summary: str
    days_considered: int
    average_precipitation_probability: int | None
    average_humidity: int | None
    max_precipitation_probability: int | None


@dataclass(frozen=True)
class RecommendationDecision:
    recommendation: str
    reason: str
    recommend_level: str
    status_image_key: str
    execution_window: str


class LaundryTimingService:
    def list_weather_regions(self) -> list[RegionPresetResponse]:
        responses: list[RegionPresetResponse] = []

        for preset in get_region_presets():
            nx, ny = latlon_to_grid(preset.latitude, preset.longitude)
            responses.append(
                RegionPresetResponse(
                    name=preset.name,
                    aliases=list(preset.aliases),
                    latitude=preset.latitude,
                    longitude=preset.longitude,
                    nx=nx,
                    ny=ny,
                    mid_land_reg_id=preset.mid_land_reg_id,
                    mid_ta_reg_id=preset.mid_ta_reg_id,
                    description=preset.description,
                )
            )

        return responses

    async def get_weekly_weather(
        self,
        *,
        region: str | None,
        address: str | None,
        address_type: str,
        nx: int | None,
        ny: int | None,
        latitude: float | None,
        longitude: float | None,
        mid_land_reg_id: str | None,
        mid_ta_reg_id: str | None,
    ) -> WeeklyWeatherResponse:
        context = await self._resolve_weather_context(
            region=region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
        )
        return await self._fetch_weekly_weather(context)

    async def build_laundry_recommendation(
        self,
        *,
        current_weight: float,
        washer_capacity: float,
        hours_since_last_wash: float,
        weight_increase: float,
        region: str | None,
        address: str | None,
        address_type: str,
        nx: int | None,
        ny: int | None,
        latitude: float | None,
        longitude: float | None,
        mid_land_reg_id: str | None,
        mid_ta_reg_id: str | None,
    ) -> LaundryRecommendationResponse:
        self._validate_numeric_input(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            hours_since_last_wash=hours_since_last_wash,
            weight_increase=weight_increase,
        )

        signal = await self._build_weather_signal(
            region=region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
        )

        load_ratio = round((current_weight / washer_capacity) * 100, 2)
        load_ratio = min(load_ratio, 100.0)
        timing_score = self._calculate_timing_score(
            load_ratio=load_ratio,
            hours_since_last_wash=hours_since_last_wash,
            weight_increase=weight_increase,
            signal=signal,
        )
        decision = self._build_decision(
            load_ratio=load_ratio,
            hours_since_last_wash=hours_since_last_wash,
            weight_increase=weight_increase,
            timing_score=timing_score,
            signal=signal,
        )
        top_considerations = self._build_considerations(
            load_ratio=load_ratio,
            hours_since_last_wash=hours_since_last_wash,
            weight_increase=weight_increase,
            signal=signal,
        )
        action_items = self._build_action_items(
            decision=decision,
            load_ratio=load_ratio,
            signal=signal,
        )

        return LaundryRecommendationResponse(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            load_ratio=load_ratio,
            weight_increase=weight_increase,
            hours_since_last_wash=hours_since_last_wash,
            rain_expected=signal.rain_expected,
            high_humidity=signal.high_humidity,
            weather_summary=signal.weather_summary,
            recommendation=decision.recommendation,
            reason=decision.reason,
            recommend_level=decision.recommend_level,  # type: ignore[arg-type]
            status_image_key=decision.status_image_key,
            execution_window=decision.execution_window,
            timing_score=timing_score,
            weather=LaundryTimingWeatherSnapshotResponse(
                source=signal.source,
                location_label=signal.location_label,
                days_considered=signal.days_considered,
                rain_expected=signal.rain_expected,
                high_humidity=signal.high_humidity,
                outdoor_drying_friendly=signal.outdoor_drying_friendly,
                weather_summary=signal.weather_summary,
                weather_error=signal.weather_error,
            ),
            top_considerations=top_considerations,
            action_items=action_items,
        )

    async def _build_weather_signal(
        self,
        *,
        region: str | None,
        address: str | None,
        address_type: str,
        nx: int | None,
        ny: int | None,
        latitude: float | None,
        longitude: float | None,
        mid_land_reg_id: str | None,
        mid_ta_reg_id: str | None,
    ) -> WeatherSignal:
        try:
            context = await self._resolve_weather_context(
                region=region or "서울",
                address=address,
                address_type=address_type,
                nx=nx,
                ny=ny,
                latitude=latitude,
                longitude=longitude,
                mid_land_reg_id=mid_land_reg_id,
                mid_ta_reg_id=mid_ta_reg_id,
            )
            weather = await self._fetch_weekly_weather(context)
            return self._extract_weather_signal(weather)
        except HTTPException:
            raise
        except (PublicDataWeatherError, VWorldGeocoderError, AirQualityError) as exc:
            return WeatherSignal(
                source="fallback",
                location_label=region or address or "서울",
                weather_error=str(exc),
                rain_expected=True,
                high_humidity=True,
                outdoor_drying_friendly=False,
                weather_summary="실시간 날씨 조회에 실패해 보수적 기준을 적용했습니다.",
                days_considered=0,
                average_precipitation_probability=None,
                average_humidity=None,
                max_precipitation_probability=None,
            )

    async def _resolve_weather_context(
        self,
        *,
        region: str | None,
        address: str | None,
        address_type: str,
        nx: int | None,
        ny: int | None,
        latitude: float | None,
        longitude: float | None,
        mid_land_reg_id: str | None,
        mid_ta_reg_id: str | None,
    ) -> ResolvedWeatherContext:
        preset = None
        resolved_latitude = latitude
        resolved_longitude = longitude
        address_hint = address

        if region:
            preset = resolve_region_preset(region)
            if preset is None:
                raise HTTPException(status_code=404, detail=f"지원하지 않는 지역입니다: {region}")

        if address and (resolved_latitude is None or resolved_longitude is None):
            if address_type not in {"auto", "road", "parcel"}:
                raise HTTPException(
                    status_code=422,
                    detail="address_type은 auto, road, parcel 중 하나여야 합니다.",
                )

            geocoded = await geocode_address(
                address=address,
                address_type=address_type,  # type: ignore[arg-type]
            )
            resolved_latitude = geocoded.latitude
            resolved_longitude = geocoded.longitude
            address_hint = geocoded.refined_text or geocoded.address

        if preset is None and resolved_latitude is not None and resolved_longitude is not None:
            preset = find_nearest_region_preset(resolved_latitude, resolved_longitude)
            if address_hint is None:
                address_hint = preset.name

        resolved_mid_land_reg_id = mid_land_reg_id or (preset.mid_land_reg_id if preset else None)
        resolved_mid_ta_reg_id = mid_ta_reg_id or (preset.mid_ta_reg_id if preset else None)
        if resolved_mid_land_reg_id is None or resolved_mid_ta_reg_id is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "mid_land_reg_id와 mid_ta_reg_id를 직접 주거나 "
                    "region, latitude/longitude, address 중 하나를 사용해야 합니다."
                ),
            )

        if nx is None or ny is None:
            if resolved_latitude is not None and resolved_longitude is not None:
                nx, ny = latlon_to_grid(resolved_latitude, resolved_longitude)
            elif preset is not None:
                nx, ny = latlon_to_grid(preset.latitude, preset.longitude)
                resolved_latitude = preset.latitude
                resolved_longitude = preset.longitude
            else:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "nx, ny를 직접 주거나 latitude, longitude, address "
                        "또는 region 프리셋을 사용해야 합니다."
                    ),
                )

        location_label = address_hint or (preset.name if preset else None)
        return ResolvedWeatherContext(
            location_label=location_label,
            address_hint=address_hint,
            latitude=resolved_latitude,
            longitude=resolved_longitude,
            nx=nx,
            ny=ny,
            mid_land_reg_id=resolved_mid_land_reg_id,
            mid_ta_reg_id=resolved_mid_ta_reg_id,
        )

    async def _fetch_weekly_weather(self, context: ResolvedWeatherContext) -> WeeklyWeatherResponse:
        weather = await get_weekly_weather(
            nx=context.nx,
            ny=context.ny,
            mid_land_reg_id=context.mid_land_reg_id,
            mid_ta_reg_id=context.mid_ta_reg_id,
        )

        current_air_quality = None
        current_air_quality_error = None
        if (
            context.latitude is not None
            and context.longitude is not None
            and context.address_hint
        ):
            try:
                air_quality = await get_current_air_quality(
                    latitude=context.latitude,
                    longitude=context.longitude,
                    address_hint=self._build_air_quality_address_hint(context.address_hint),
                )
            except AirQualityError as exc:
                current_air_quality_error = str(exc)
                air_quality = None

            if air_quality is not None:
                current_air_quality = AirQualityResponse.model_validate(air_quality.__dict__)

        weather["current_air_quality"] = current_air_quality
        weather["current_air_quality_error"] = current_air_quality_error
        weather["location"]["label"] = context.location_label or ""
        return WeeklyWeatherResponse.model_validate(weather)

    def _extract_weather_signal(self, weather: WeeklyWeatherResponse) -> WeatherSignal:
        near_term_days = weather.days[:3]
        precipitation_values = [
            day.precipitation_probability
            for day in near_term_days
            if day.precipitation_probability is not None
        ]
        humidity_values = [
            day.relative_humidity
            for day in near_term_days
            if day.relative_humidity is not None
        ]

        rain_expected = any(
            (day.precipitation_probability or 0) >= 60 or self._summary_mentions_precipitation(day.summary)
            for day in near_term_days
        )
        high_humidity = any((day.relative_humidity or 0) >= 75 for day in near_term_days)
        outdoor_drying_friendly = any(
            (day.precipitation_probability or 0) <= 30
            and (day.relative_humidity or 100) <= 60
            and not self._summary_mentions_precipitation(day.summary)
            for day in near_term_days
        )

        summaries = [day.summary for day in near_term_days if day.summary]
        if rain_expected and high_humidity:
            weather_summary = "가까운 시일 내 비 예보와 높은 습도가 함께 예상됩니다."
        elif rain_expected:
            weather_summary = "가까운 시일 내 비 예보가 있어 건조 여건이 나빠질 수 있습니다."
        elif high_humidity:
            weather_summary = "습도가 높아 자연 건조 시간이 길어질 가능성이 있습니다."
        elif outdoor_drying_friendly:
            weather_summary = "자연 건조에 유리한 날이 가까운 시일 내 포함되어 있습니다."
        elif summaries:
            weather_summary = summaries[0]
        else:
            weather_summary = "예보 요약 정보가 제한적이어서 보수적으로 판단합니다."

        return WeatherSignal(
            source="forecast",
            location_label=self._extract_location_label(weather),
            weather_error=weather.current_air_quality_error,
            rain_expected=rain_expected,
            high_humidity=high_humidity,
            outdoor_drying_friendly=outdoor_drying_friendly,
            weather_summary=weather_summary,
            days_considered=len(near_term_days),
            average_precipitation_probability=(
                round(sum(precipitation_values) / len(precipitation_values))
                if precipitation_values
                else None
            ),
            average_humidity=(
                round(sum(humidity_values) / len(humidity_values))
                if humidity_values
                else None
            ),
            max_precipitation_probability=max(precipitation_values) if precipitation_values else None,
        )

    def _calculate_timing_score(
        self,
        *,
        load_ratio: float,
        hours_since_last_wash: float,
        weight_increase: float,
        signal: WeatherSignal,
    ) -> int:
        load_component = min(45, round(load_ratio * 0.45))
        interval_component = min(30, round(min(hours_since_last_wash, 120) / 4))
        growth_component = min(15, round(min(weight_increase, 1.5) * 10))
        weather_component = 0

        if signal.rain_expected:
            weather_component += 8
        if signal.high_humidity:
            weather_component += 7
        if not signal.outdoor_drying_friendly:
            weather_component += 5

        return min(100, load_component + interval_component + growth_component + weather_component)

    def _build_decision(
        self,
        *,
        load_ratio: float,
        hours_since_last_wash: float,
        weight_increase: float,
        timing_score: int,
        signal: WeatherSignal,
    ) -> RecommendationDecision:
        if load_ratio >= 85 or hours_since_last_wash >= 96:
            return RecommendationDecision(
                recommendation="지금 세탁 추천",
                reason="적재율이 높거나 세탁 공백이 길어 더 미루기 어렵습니다.",
                recommend_level="high",
                status_image_key="wash_now",
                execution_window="가능하면 지금 바로",
            )

        if (load_ratio >= 65 and (signal.rain_expected or signal.high_humidity)) or timing_score >= 75:
            return RecommendationDecision(
                recommendation="오늘 안에 세탁 추천",
                reason="세탁물이 쌓인 상태에서 건조 여건이 더 나빠질 가능성이 있어 오늘 처리하는 편이 좋습니다.",
                recommend_level="high",
                status_image_key="wash_today",
                execution_window="오늘 저녁 전",
            )

        if (signal.rain_expected or signal.high_humidity) and (load_ratio >= 40 or hours_since_last_wash >= 36):
            return RecommendationDecision(
                recommendation="곧 세탁 추천",
                reason="세탁량은 과하지 않지만 가까운 시일 내 건조 환경이 좋지 않아 너무 늦추지 않는 편이 안전합니다.",
                recommend_level="medium",
                status_image_key="wash_soon",
                execution_window="다음 24시간 안",
            )

        if signal.outdoor_drying_friendly and load_ratio < 55 and hours_since_last_wash < 72:
            return RecommendationDecision(
                recommendation="내일 오전 세탁 추천",
                reason="아직 급한 수준은 아니지만 가까운 시일 내 자연 건조에 유리한 창이 있습니다.",
                recommend_level="low",
                status_image_key="wash_tomorrow",
                execution_window="다음 맑은 날 오전",
            )

        if load_ratio >= 50 or weight_increase >= 1.0 or hours_since_last_wash >= 72:
            return RecommendationDecision(
                recommendation="곧 세탁 추천",
                reason="적재량과 경과 시간 기준으로 세탁 필요도가 점차 높아지고 있습니다.",
                recommend_level="medium",
                status_image_key="wash_soon",
                execution_window="오늘 또는 내일",
            )

        return RecommendationDecision(
            recommendation="아직 세탁 필요 없음",
            reason="현재 적재량과 세탁 간격 기준으로는 조금 더 모아도 무리가 없습니다.",
            recommend_level="low",
            status_image_key="wait",
            execution_window="다음 세탁 주기까지 대기",
        )

    def _build_considerations(
        self,
        *,
        load_ratio: float,
        hours_since_last_wash: float,
        weight_increase: float,
        signal: WeatherSignal,
    ) -> list[LaundryTimingConsiderationResponse]:
        considerations = [
            LaundryTimingConsiderationResponse(
                category="적재량",
                score=min(100, round(load_ratio)),
                summary=self._summarize_load_ratio(load_ratio),
                details=[
                    f"현재 적재율은 {load_ratio:.2f}%입니다.",
                    "적재율이 높을수록 세탁 지연 시 냄새와 보관 부담이 커집니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="세탁 공백",
                score=min(100, round(hours_since_last_wash / 1.2)),
                summary=self._summarize_wash_interval(hours_since_last_wash),
                details=[
                    f"마지막 세탁 후 {hours_since_last_wash:.1f}시간 경과했습니다.",
                    "세탁 주기가 길어질수록 다음 회차 적재율이 급격히 올라갈 수 있습니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="적재 증가 속도",
                score=min(100, round(weight_increase * 45)),
                summary=self._summarize_weight_increase(weight_increase),
                details=[
                    f"최근 증가한 세탁물 무게는 {weight_increase:.2f}kg입니다.",
                    "증가 속도가 빠르면 예상보다 빨리 세탁 시점을 맞게 됩니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="건조 환경",
                score=self._calculate_weather_pressure(signal),
                summary=signal.weather_summary,
                details=[
                    "비 예보와 습도는 세탁 후 건조 난이도에 직접적인 영향을 줍니다.",
                    f"가까운 시일 내 비 예보 여부: {'예상됨' if signal.rain_expected else '크지 않음'}",
                    f"고습도 여부: {'높음' if signal.high_humidity else '보통'}",
                ],
            ),
        ]

        return sorted(considerations, key=lambda item: item.score, reverse=True)[:3]

    def _build_action_items(
        self,
        *,
        decision: RecommendationDecision,
        load_ratio: float,
        signal: WeatherSignal,
    ) -> list[str]:
        actions: list[str] = []

        if decision.recommend_level == "high":
            actions.append("세탁을 미루지 말고 오늘 안에 한 번 돌리는 편이 좋습니다.")
        elif decision.recommend_level == "medium":
            actions.append("다음 24시간 안에 세탁 일정을 잡아두는 것을 권장합니다.")
        else:
            actions.append("급하지 않다면 세탁물을 조금 더 모아도 괜찮습니다.")

        if load_ratio >= 80:
            actions.append("적재율이 높으니 세탁망 분리나 2회 분할 세탁도 함께 고려하세요.")

        if signal.rain_expected or signal.high_humidity:
            actions.append("실내 건조 공간이나 건조기 사용 가능 여부를 먼저 확인해두세요.")
        elif signal.outdoor_drying_friendly:
            actions.append("자연 건조가 가능한 시간대에 맞춰 오전 세탁으로 잡으면 효율적입니다.")

        if not actions:
            actions.append("현재 패턴을 유지하면서 다음 적재 증가만 지켜보면 됩니다.")

        return actions

    def _validate_numeric_input(
        self,
        *,
        current_weight: float,
        washer_capacity: float,
        hours_since_last_wash: float,
        weight_increase: float,
    ) -> None:
        if current_weight <= 0:
            raise HTTPException(status_code=422, detail="current_weight는 0보다 커야 합니다.")
        if washer_capacity <= 0:
            raise HTTPException(status_code=422, detail="washer_capacity는 0보다 커야 합니다.")
        if hours_since_last_wash < 0:
            raise HTTPException(status_code=422, detail="hours_since_last_wash는 음수일 수 없습니다.")
        if weight_increase < 0:
            raise HTTPException(status_code=422, detail="weight_increase는 음수일 수 없습니다.")

    def _calculate_weather_pressure(self, signal: WeatherSignal) -> int:
        score = 20
        if signal.rain_expected:
            score += 35
        if signal.high_humidity:
            score += 25
        if not signal.outdoor_drying_friendly:
            score += 10
        return min(score, 100)

    def _summarize_load_ratio(self, load_ratio: float) -> str:
        if load_ratio >= 80:
            return "세탁기를 곧 돌려야 할 만큼 적재율이 높습니다."
        if load_ratio >= 60:
            return "세탁 시점을 본격적으로 잡아야 하는 수준입니다."
        if load_ratio >= 40:
            return "아직 여유는 있지만 빠르게 쌓일 수 있습니다."
        return "적재량만 보면 아직 급한 편은 아닙니다."

    def _summarize_wash_interval(self, hours_since_last_wash: float) -> str:
        if hours_since_last_wash >= 96:
            return "세탁 주기가 길어져 바로 처리하는 편이 좋습니다."
        if hours_since_last_wash >= 72:
            return "세탁 공백이 길어져 다음 세탁 시점을 준비해야 합니다."
        if hours_since_last_wash >= 48:
            return "이틀 이상 경과해 중간 이상 우선순위로 볼 수 있습니다."
        return "마지막 세탁 이후 경과 시간은 아직 짧은 편입니다."

    def _summarize_weight_increase(self, weight_increase: float) -> str:
        if weight_increase >= 1.2:
            return "세탁물 증가 속도가 빨라 조기 세탁이 유리합니다."
        if weight_increase >= 0.7:
            return "세탁물이 꾸준히 늘고 있어 다음 회차가 멀지 않았습니다."
        return "최근 적재 증가 속도는 비교적 완만합니다."

    def _summary_mentions_precipitation(self, summary: str | None) -> bool:
        if not summary:
            return False
        return any(keyword in summary for keyword in ("비", "눈", "소나기", "빗방울"))

    def _extract_location_label(self, weather: WeeklyWeatherResponse) -> str | None:
        location = weather.location
        if "label" in location and location["label"]:
            return str(location["label"])
        label_parts = [
            str(location[key])
            for key in ("mid_land_reg_id", "mid_ta_reg_id")
            if key in location
        ]
        if not label_parts:
            return None
        return " / ".join(label_parts)

    def _build_air_quality_address_hint(self, address: str) -> str:
        tokens = [token for token in address.split() if token]
        if len(tokens) >= 2:
            return " ".join(tokens[:2])
        return address
