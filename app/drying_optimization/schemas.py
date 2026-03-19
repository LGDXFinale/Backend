from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DryRecommendLevel = Literal["low", "medium", "high"]
OdorRiskLevel = Literal["low", "medium", "high"]


class DryAirQualityResponse(BaseModel):
    source: str = Field(..., description="Air quality data source")
    source_label: str = Field(..., description="Air quality data source label")
    outdoor_safe: bool = Field(..., description="Whether outdoor drying is acceptable")
    outdoor_safe_label: str = Field(..., description="Outdoor drying safety label")
    station_name: str | None = Field(None, description="Nearest monitoring station")
    station_address: str | None = Field(None, description="Monitoring station address")
    measured_at: str | None = Field(None, description="Measurement timestamp")
    pm10: int | None = Field(None, description="PM10 concentration")
    pm10_grade: str | None = Field(None, description="PM10 grade")
    pm25: int | None = Field(None, description="PM2.5 concentration")
    pm25_grade: str | None = Field(None, description="PM2.5 grade")
    error: str | None = Field(None, description="Air quality lookup error")


class DryWeatherDayResponse(BaseModel):
    date: str = Field(..., description="Forecast date")
    summary: str | None = Field(None, description="Forecast summary")
    precipitation_probability: int | None = Field(None, description="Rain probability")
    relative_humidity: int | None = Field(None, description="Relative humidity")
    min_temp: float | None = Field(None, description="Minimum temperature")
    max_temp: float | None = Field(None, description="Maximum temperature")
    drying_friendly: bool = Field(..., description="Whether the day is outdoor-drying friendly")
    drying_friendly_label: str = Field(..., description="Outdoor-drying-friendly label")


class DryWeatherInfoResponse(BaseModel):
    source: str = Field(..., description="Weather data source")
    source_label: str = Field(..., description="Weather data source label")
    location_label: str = Field(..., description="Resolved location label")
    weather_summary: str = Field(..., description="Weather summary used for drying")
    weather_main: str | None = Field(None, description="Representative weather category")
    weather_main_label: str | None = Field(None, description="Representative weather category label")
    weather_description: str | None = Field(None, description="Detailed weather description")
    is_raining: bool = Field(..., description="Whether rain is expected soon")
    humidity: int = Field(..., ge=0, le=100, description="Representative outdoor humidity")
    temperature: float = Field(..., description="Representative outdoor temperature")
    wind_speed_mps: float | None = Field(None, description="Representative wind speed")
    weather_error: str | None = Field(None, description="Weather lookup error")
    rain_expected: bool = Field(..., description="Whether near-term rain is expected")
    high_humidity: bool = Field(..., description="Whether near-term humidity is high")
    outdoor_drying_friendly: bool = Field(..., description="Whether today is good for outdoor drying")
    favorable_day_offset: int | None = Field(None, description="Days until the next favorable outdoor day")
    favorable_day_summary: str | None = Field(None, description="Summary of the next favorable outdoor day")
    air_quality: DryAirQualityResponse | None = Field(None, description="Air quality information")
    forecast_days: list[DryWeatherDayResponse] = Field(..., description="Forecast days used for the decision")


class IndoorEnvironmentResponse(BaseModel):
    indoor_humidity: int = Field(..., ge=0, le=100, description="Indoor humidity")
    indoor_temperature: float = Field(..., description="Indoor temperature")
    airflow_level: int = Field(..., ge=0, le=100, description="Indoor airflow score")
    dehumidifier_on: bool = Field(..., description="Whether a dehumidifier is on")


class MoistureEstimationResponse(BaseModel):
    estimated_moisture_percent: int = Field(..., ge=0, le=100, description="Estimated moisture percentage")
    residual_water_kg: float = Field(..., ge=0, description="Estimated residual water weight")
    weight_change_kg: float | None = Field(None, description="Measured weight reduction after spinning")
    final_spin_rpm: int = Field(..., ge=0, description="Final spin RPM")
    odor_risk_level: OdorRiskLevel = Field(..., description="Odor risk")
    odor_risk_level_label: str = Field(..., description="Odor risk label")


class DryEnvironmentAnalysisResponse(BaseModel):
    indoor_score: int = Field(..., ge=0, le=100, description="Indoor drying score")
    outdoor_score: int = Field(..., ge=0, le=100, description="Outdoor drying score")
    preferred_environment: str = Field(..., description="Preferred drying environment")
    preferred_environment_label: str = Field(..., description="Preferred drying environment label")
    summary: str = Field(..., description="Environment comparison summary")


class DryingConsiderationResponse(BaseModel):
    category: str = Field(..., description="Decision category")
    score: int = Field(..., ge=0, le=100, description="Decision score")
    summary: str = Field(..., description="Summary")
    details: list[str] = Field(..., description="Detailed reasons")


class DryRecommendationResponse(BaseModel):
    generated_at: str = Field(..., description="Response generation timestamp")
    member_id: str = Field(..., description="Member id")
    washer_id: str = Field(..., description="Washer id")
    dry_rec_id: str = Field(..., description="Recommendation id")
    dry_rec_time: int = Field(..., ge=0, description="Estimated drying time in minutes")
    dry_rec_method: int = Field(..., ge=1, le=4, description="Drying method code")
    dry_rec_method_name: str = Field(..., description="Drying method name")
    recommendation: str = Field(..., description="Recommendation headline")
    reason: str = Field(..., description="Recommendation reason")
    recommend_level: DryRecommendLevel = Field(..., description="Recommendation level")
    recommend_level_label: str = Field(..., description="Recommendation level label")
    status_image_key: str = Field(..., description="Status image key")
    caution: str = Field(..., description="Caution message")
    energy_tip: str = Field(..., description="Energy saving tip")
    weather_info: DryWeatherInfoResponse = Field(..., description="Weather snapshot")
    indoor_environment: IndoorEnvironmentResponse = Field(..., description="Indoor environment")
    moisture_estimation: MoistureEstimationResponse = Field(..., description="Moisture estimate")
    environment_analysis: DryEnvironmentAnalysisResponse = Field(..., description="Environment analysis")
    top_considerations: list[DryingConsiderationResponse] = Field(..., description="Top considerations")
    action_items: list[str] = Field(..., description="Suggested action items")
