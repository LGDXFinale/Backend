from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fastapi import HTTPException

from app.laundry_timing.schemas import (
    AirQualityResponse,
    CurrentLoadResponse,
    FutureLoadPredictionResponse,
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
class LoadSnapshot:
    current_weight: float
    washer_capacity: float
    load_ratio: float
    washer_inner_weight_kg: float
    washer_inner_load_ratio: float
    basket_weight_kg: float
    load_source: str
    basket_sensor_weight_kg: float | None
    note: str


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

    def get_current_load_snapshot(
        self,
        *,
        member_id: str,
        washer_id: str,
        current_weight: float,
        washer_capacity: float,
        basket_sensor_weight_kg: float | None,
        manual_refresh: bool,
    ) -> CurrentLoadResponse:
        self._validate_numeric_input(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            weight_increase=0,
            hours_since_last_wash=0,
            household_size=1,
            urgent_clothing_count=0,
            forecast_hours=24,
        )
        snapshot = self._build_load_snapshot(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            basket_sensor_weight_kg=basket_sensor_weight_kg,
        )
        return CurrentLoadResponse(
            member_id=member_id,
            washer_id=washer_id,
            measured_at=datetime.now().isoformat(timespec="seconds"),
            current_weight=snapshot.current_weight,
            washer_capacity=snapshot.washer_capacity,
            load_ratio=snapshot.load_ratio,
            washer_inner_weight_kg=snapshot.washer_inner_weight_kg,
            washer_inner_load_ratio=snapshot.washer_inner_load_ratio,
            basket_weight_kg=snapshot.basket_weight_kg,
            load_source=snapshot.load_source,  # type: ignore[arg-type]
            manual_refresh=manual_refresh,
            basket_sensor_weight_kg=snapshot.basket_sensor_weight_kg,
            note=snapshot.note,
        )

    async def predict_future_load(
        self,
        *,
        member_id: str,
        washer_id: str,
        current_weight: float,
        washer_capacity: float,
        household_size: int,
        hours_ahead: int,
        weight_increase: float,
        urgent_clothing_count: int,
        basket_sensor_weight_kg: float | None,
        region: str | None,
        address: str | None,
        address_type: str,
        nx: int | None,
        ny: int | None,
        latitude: float | None,
        longitude: float | None,
        mid_land_reg_id: str | None,
        mid_ta_reg_id: str | None,
    ) -> FutureLoadPredictionResponse:
        self._validate_numeric_input(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            weight_increase=weight_increase,
            hours_since_last_wash=0,
            household_size=household_size,
            urgent_clothing_count=urgent_clothing_count,
            forecast_hours=hours_ahead,
        )
        snapshot = self._build_load_snapshot(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            basket_sensor_weight_kg=basket_sensor_weight_kg,
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
        return self._build_future_prediction(
            member_id=member_id,
            washer_id=washer_id,
            snapshot=snapshot,
            household_size=household_size,
            hours_ahead=hours_ahead,
            weight_increase=weight_increase,
            urgent_clothing_count=urgent_clothing_count,
            signal=signal,
        )

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
        member_id: str,
        washer_id: str,
        current_weight: float,
        washer_capacity: float,
        hours_since_last_wash: float,
        weight_increase: float,
        household_size: int,
        urgent_clothing_count: int,
        basket_sensor_weight_kg: float | None,
        manual_refresh: bool,
        forecast_hours: int,
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
            weight_increase=weight_increase,
            hours_since_last_wash=hours_since_last_wash,
            household_size=household_size,
            urgent_clothing_count=urgent_clothing_count,
            forecast_hours=forecast_hours,
        )
        snapshot = self._build_load_snapshot(
            current_weight=current_weight,
            washer_capacity=washer_capacity,
            basket_sensor_weight_kg=basket_sensor_weight_kg,
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
        future_prediction = self._build_future_prediction(
            member_id=member_id,
            washer_id=washer_id,
            snapshot=snapshot,
            household_size=household_size,
            hours_ahead=forecast_hours,
            weight_increase=weight_increase,
            urgent_clothing_count=urgent_clothing_count,
            signal=signal,
        )
        urgency_score = self._calculate_urgency_score(
            urgent_clothing_count=urgent_clothing_count,
            hours_since_last_wash=hours_since_last_wash,
        )
        timing_score = self._calculate_timing_score(
            load_ratio=snapshot.load_ratio,
            future_load_ratio=future_prediction.predicted_load_ratio,
            hours_since_last_wash=hours_since_last_wash,
            urgency_score=urgency_score,
            signal=signal,
        )
        decision = self._build_decision(
            load_ratio=snapshot.load_ratio,
            future_load_ratio=future_prediction.predicted_load_ratio,
            hours_since_last_wash=hours_since_last_wash,
            urgency_score=urgency_score,
            signal=signal,
            timing_score=timing_score,
        )
        considerations = self._build_considerations(
            snapshot=snapshot,
            future_prediction=future_prediction,
            hours_since_last_wash=hours_since_last_wash,
            urgency_score=urgency_score,
            urgent_clothing_count=urgent_clothing_count,
            signal=signal,
        )
        action_items = self._build_action_items(
            decision=decision,
            snapshot=snapshot,
            future_prediction=future_prediction,
            signal=signal,
            manual_refresh=manual_refresh,
        )
        return LaundryRecommendationResponse(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            member_id=member_id,
            washer_id=washer_id,
            current_weight=snapshot.current_weight,
            washer_capacity=snapshot.washer_capacity,
            load_ratio=snapshot.load_ratio,
            weight_increase=weight_increase,
            hours_since_last_wash=hours_since_last_wash,
            household_size=household_size,
            urgent_clothing_count=urgent_clothing_count,
            urgency_score=urgency_score,
            rain_expected=signal.rain_expected,
            high_humidity=signal.high_humidity,
            weather_summary=signal.weather_summary,
            recommendation=decision.recommendation,
            reason=decision.reason,
            recommend_level=decision.recommend_level,  # type: ignore[arg-type]
            status_image_key=decision.status_image_key,
            execution_window=decision.execution_window,
            timing_score=timing_score,
            current_load=CurrentLoadResponse(
                member_id=member_id,
                washer_id=washer_id,
                measured_at=datetime.now().isoformat(timespec="seconds"),
                current_weight=snapshot.current_weight,
                washer_capacity=snapshot.washer_capacity,
                load_ratio=snapshot.load_ratio,
                washer_inner_weight_kg=snapshot.washer_inner_weight_kg,
                washer_inner_load_ratio=snapshot.washer_inner_load_ratio,
                basket_weight_kg=snapshot.basket_weight_kg,
                load_source=snapshot.load_source,  # type: ignore[arg-type]
                manual_refresh=manual_refresh,
                basket_sensor_weight_kg=snapshot.basket_sensor_weight_kg,
                note=snapshot.note,
            ),
            future_load_prediction=future_prediction,
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
            top_considerations=considerations,
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

        if context.latitude is not None and context.longitude is not None and context.address_hint:
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

    def _build_load_snapshot(
        self,
        *,
        current_weight: float,
        washer_capacity: float,
        basket_sensor_weight_kg: float | None,
    ) -> LoadSnapshot:
        resolved_weight = current_weight
        basket_weight = (
            basket_sensor_weight_kg
            if basket_sensor_weight_kg is not None and basket_sensor_weight_kg > 0
            else 0.0
        )
        basket_weight = round(min(basket_weight, resolved_weight), 2)
        washer_inner_weight = round(max(resolved_weight - basket_weight, 0.0), 2)
        load_source = "sensor" if basket_weight > 0 else "manual"
        load_ratio = round(min((resolved_weight / washer_capacity) * 100, 100), 2)
        washer_inner_load_ratio = round(min((washer_inner_weight / washer_capacity) * 100, 100), 2)

        if basket_weight > 0 and washer_inner_weight > 0:
            note = "Separated washer-inner load and basket load for display."
        elif basket_weight > 0:
            note = "Basket load is available from the sensor reading."
        elif load_ratio >= 80:
            note = "Manual load looks high enough to recommend washing soon."
        else:
            note = "Manual load is still manageable for now."

        return LoadSnapshot(
            current_weight=resolved_weight,
            washer_capacity=washer_capacity,
            load_ratio=load_ratio,
            washer_inner_weight_kg=washer_inner_weight,
            washer_inner_load_ratio=washer_inner_load_ratio,
            basket_weight_kg=basket_weight,
            load_source=load_source,
            basket_sensor_weight_kg=basket_sensor_weight_kg,
            note=note,
        )

    def _build_future_prediction(
        self,
        *,
        member_id: str,
        washer_id: str,
        snapshot: LoadSnapshot,
        household_size: int,
        hours_ahead: int,
        weight_increase: float,
        urgent_clothing_count: int,
        signal: WeatherSignal,
    ) -> FutureLoadPredictionResponse:
        base_daily_gain = 0.35 + max(household_size - 1, 0) * 0.22
        recent_gain_bonus = min(weight_increase, 1.5) * 0.45
        weather_delay_bonus = (0.18 if signal.rain_expected else 0.0) + (
            0.12 if signal.high_humidity else 0.0
        )
        accumulation_speed = round(base_daily_gain + recent_gain_bonus + weather_delay_bonus, 2)
        urgency_adjustment_score = min(100, urgent_clothing_count * 18)

        predicted_weight = round(
            min(
                snapshot.washer_capacity,
                snapshot.current_weight + accumulation_speed * (hours_ahead / 24),
            ),
            2,
        )
        predicted_load_ratio = round(min((predicted_weight / snapshot.washer_capacity) * 100, 100), 2)

        if predicted_load_ratio >= 85:
            forecast_summary = "예측 범위 안에 적재율이 빠르게 높아질 가능성이 큽니다."
        elif urgent_clothing_count > 0:
            forecast_summary = "적재율 자체는 중간이지만 긴급 의류가 있어 세탁 시점이 앞당겨질 수 있습니다."
        elif signal.rain_expected or signal.high_humidity:
            forecast_summary = "건조 여건 악화 가능성 때문에 세탁물이 더 쌓일수록 대응 폭이 줄어듭니다."
        else:
            forecast_summary = "현재 증가 속도 기준으로는 완만하게 적재량이 늘어날 것으로 보입니다."

        return FutureLoadPredictionResponse(
            member_id=member_id,
            washer_id=washer_id,
            calculated_at=datetime.now().isoformat(timespec="seconds"),
            calculation_basis="현재 적재량, 최근 증가량, 가구원 수, 긴급 의류 수, 날씨 데이터를 기반으로 요청 시점에 계산한 예측값입니다.",
            forecast_hours=hours_ahead,
            household_size=household_size,
            accumulation_speed_kg_per_day=accumulation_speed,
            predicted_weight_kg=predicted_weight,
            predicted_load_ratio=predicted_load_ratio,
            urgency_adjustment_score=urgency_adjustment_score,
            forecast_summary=forecast_summary,
        )

    def _extract_weather_signal(self, weather: WeeklyWeatherResponse) -> WeatherSignal:
        near_term_days = weather.days[:3]
        precipitation_values = [
            day.precipitation_probability
            for day in near_term_days
            if day.precipitation_probability is not None
        ]
        humidity_values = [
            day.relative_humidity for day in near_term_days if day.relative_humidity is not None
        ]
        rain_expected = any(
            (day.precipitation_probability or 0) >= 60
            or self._summary_mentions_precipitation(day.summary)
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
                round(sum(humidity_values) / len(humidity_values)) if humidity_values else None
            ),
            max_precipitation_probability=max(precipitation_values) if precipitation_values else None,
        )

    def _calculate_urgency_score(
        self,
        *,
        urgent_clothing_count: int,
        hours_since_last_wash: float,
    ) -> int:
        score = urgent_clothing_count * 22
        if hours_since_last_wash >= 72:
            score += 12
        return min(score, 100)

    def _calculate_timing_score(
        self,
        *,
        load_ratio: float,
        future_load_ratio: float,
        hours_since_last_wash: float,
        urgency_score: int,
        signal: WeatherSignal,
    ) -> int:
        current_load_component = min(35, round(load_ratio * 0.35))
        future_load_component = min(30, round(future_load_ratio * 0.3))
        interval_component = min(15, round(min(hours_since_last_wash, 120) / 8))
        weather_component = 0
        if signal.rain_expected:
            weather_component += 8
        if signal.high_humidity:
            weather_component += 7
        if not signal.outdoor_drying_friendly:
            weather_component += 5
        urgency_component = min(15, round(urgency_score * 0.15))
        return min(
            100,
            current_load_component
            + future_load_component
            + interval_component
            + weather_component
            + urgency_component,
        )

    def _build_decision(
        self,
        *,
        load_ratio: float,
        future_load_ratio: float,
        hours_since_last_wash: float,
        urgency_score: int,
        signal: WeatherSignal,
        timing_score: int,
    ) -> RecommendationDecision:
        if urgency_score >= 60 or load_ratio >= 85:
            return RecommendationDecision(
                recommendation="즉시 세탁 추천",
                reason="긴급 의류가 많거나 현재 적재율이 높아 더 미루기 어렵습니다.",
                recommend_level="high",
                status_image_key="wash_now",
                execution_window="가능하면 지금 바로",
            )
        if future_load_ratio >= 85 or timing_score >= 75:
            return RecommendationDecision(
                recommendation="조기 세탁 추천",
                reason="가까운 시일 내 적재율이 크게 높아질 가능성이 있어 미리 처리하는 편이 좋습니다.",
                recommend_level="high",
                status_image_key="wash_early",
                execution_window="오늘 안",
            )
        if (signal.rain_expected or signal.high_humidity) and (load_ratio >= 45 or future_load_ratio >= 65):
            return RecommendationDecision(
                recommendation="오늘 안에 세탁 추천",
                reason="건조 여건이 나빠질 가능성이 있어 세탁 시점을 앞당기는 편이 안전합니다.",
                recommend_level="medium",
                status_image_key="wash_today",
                execution_window="다음 24시간 안",
            )
        if hours_since_last_wash >= 72 or future_load_ratio >= 60:
            return RecommendationDecision(
                recommendation="곧 세탁 추천",
                reason="적재량과 세탁 간격 기준으로 다음 세탁 시점을 준비해야 합니다.",
                recommend_level="medium",
                status_image_key="wash_soon",
                execution_window="오늘 또는 내일",
            )
        return RecommendationDecision(
            recommendation="대기",
            reason="현재 적재량과 미래 예측 기준으로는 조금 더 지켜봐도 괜찮습니다.",
            recommend_level="low",
            status_image_key="wait",
            execution_window="다음 세탁 주기까지 대기",
        )

    def _build_considerations(
        self,
        *,
        snapshot: LoadSnapshot,
        future_prediction: FutureLoadPredictionResponse,
        hours_since_last_wash: float,
        urgency_score: int,
        urgent_clothing_count: int,
        signal: WeatherSignal,
    ) -> list[LaundryTimingConsiderationResponse]:
        considerations = [
            LaundryTimingConsiderationResponse(
                category="현재 적재량",
                score=min(100, round(snapshot.load_ratio)),
                summary=self._summarize_load_ratio(snapshot.load_ratio),
                details=[
                    f"현재 적재율은 {snapshot.load_ratio:.2f}%입니다.",
                    f"측정 출처는 {snapshot.load_source}입니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="미래 적재량 예측",
                score=min(100, round(future_prediction.predicted_load_ratio)),
                summary=future_prediction.forecast_summary,
                details=[
                    f"{future_prediction.forecast_hours}시간 뒤 예상 적재율은 {future_prediction.predicted_load_ratio:.2f}%입니다.",
                    f"하루 적재 증가량 예측은 {future_prediction.accumulation_speed_kg_per_day:.2f}kg입니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="세탁 긴급도",
                score=urgency_score,
                summary=self._summarize_urgency(urgent_clothing_count, urgency_score),
                details=[
                    f"긴급 세탁 의류 수는 {urgent_clothing_count}개입니다.",
                    f"마지막 세탁 후 {hours_since_last_wash:.1f}시간 경과했습니다.",
                ],
            ),
            LaundryTimingConsiderationResponse(
                category="날씨 영향",
                score=self._calculate_weather_pressure(signal),
                summary=signal.weather_summary,
                details=[
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
        snapshot: LoadSnapshot,
        future_prediction: FutureLoadPredictionResponse,
        signal: WeatherSignal,
        manual_refresh: bool,
    ) -> list[str]:
        actions: list[str] = []
        if manual_refresh:
            actions.append("수동 새로고침 기준 최신 적재량을 반영했습니다.")
        if snapshot.load_source == "manual":
            actions.append("센서 연동 전까지는 현재 적재량을 주기적으로 다시 입력해주면 예측 정확도가 좋아집니다.")
        if decision.recommend_level == "high":
            actions.append("세탁을 미루지 말고 가까운 시간 안에 한 번 돌리는 편이 좋습니다.")
        elif decision.recommend_level == "medium":
            actions.append("다음 24시간 안에 세탁 일정을 잡아두는 것을 권장합니다.")
        else:
            actions.append("지금은 대기해도 되지만, 적재량이 빠르게 증가하면 다시 확인해보세요.")
        if future_prediction.predicted_load_ratio >= 80:
            actions.append("예상 적재율이 높아질 수 있으니 세탁망 분리나 2회 분할 세탁도 고려하세요.")
        if signal.rain_expected or signal.high_humidity:
            actions.append("건조 여건이 나빠질 수 있으니 실내 건조 공간도 함께 확인해두세요.")
        elif signal.outdoor_drying_friendly:
            actions.append("맑은 시간대에 맞춰 세탁하면 자연 건조 효율을 높일 수 있습니다.")
        return actions

    def _validate_numeric_input(
        self,
        *,
        current_weight: float,
        washer_capacity: float,
        weight_increase: float,
        hours_since_last_wash: float,
        household_size: int,
        urgent_clothing_count: int,
        forecast_hours: int,
    ) -> None:
        if current_weight <= 0:
            raise HTTPException(status_code=422, detail="current_weight는 0보다 커야 합니다.")
        if washer_capacity <= 0:
            raise HTTPException(status_code=422, detail="washer_capacity는 0보다 커야 합니다.")
        if weight_increase < 0:
            raise HTTPException(status_code=422, detail="weight_increase는 음수일 수 없습니다.")
        if hours_since_last_wash < 0:
            raise HTTPException(status_code=422, detail="hours_since_last_wash는 음수일 수 없습니다.")
        if household_size < 1:
            raise HTTPException(status_code=422, detail="household_size는 1 이상이어야 합니다.")
        if urgent_clothing_count < 0:
            raise HTTPException(status_code=422, detail="urgent_clothing_count는 음수일 수 없습니다.")
        if forecast_hours < 1:
            raise HTTPException(status_code=422, detail="forecast_hours는 1 이상이어야 합니다.")

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

    def _summarize_urgency(self, urgent_clothing_count: int, urgency_score: int) -> str:
        if urgent_clothing_count >= 3 or urgency_score >= 60:
            return "긴급 세탁 의류가 많아 대기보다는 즉시 처리 쪽이 유리합니다."
        if urgent_clothing_count > 0:
            return "일부 의류는 우선 세탁 대상이라 시점을 너무 늦추지 않는 편이 좋습니다."
        return "긴급 의류 요인은 아직 크지 않습니다."

    def _summary_mentions_precipitation(self, summary: str | None) -> bool:
        return bool(summary) and any(keyword in summary for keyword in ("비", "눈", "소나기", "빗방울"))

    def _extract_location_label(self, weather: WeeklyWeatherResponse) -> str | None:
        location = weather.location
        if "label" in location and location["label"]:
            return str(location["label"])
        label_parts = [str(location[key]) for key in ("mid_land_reg_id", "mid_ta_reg_id") if key in location]
        return " / ".join(label_parts) if label_parts else None

    def _build_air_quality_address_hint(self, address: str) -> str:
        tokens = [token for token in address.split() if token]
        return " ".join(tokens[:2]) if len(tokens) >= 2 else address
