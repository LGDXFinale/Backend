from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherDayResponse(BaseModel):
    date: str
    source: str
    min_temp: float | None
    max_temp: float | None
    precipitation_probability: int | None
    relative_humidity: int | None
    feels_like_temp: float | None
    summary: str | None


class AirQualityResponse(BaseModel):
    station_name: str
    station_address: str | None
    measured_at: str | None
    pm10: int | None
    pm10_grade: str | None
    pm25: int | None
    pm25_grade: str | None
    source: str


class WeeklyWeatherResponse(BaseModel):
    generated_at: str
    location: dict[str, str | int]
    sources: dict[str, str]
    current_air_quality: AirQualityResponse | None = None
    current_air_quality_error: str | None = None
    days: list[WeatherDayResponse]


class RegionPresetResponse(BaseModel):
    name: str
    aliases: list[str]
    latitude: float
    longitude: float
    nx: int
    ny: int
    mid_land_reg_id: str
    mid_ta_reg_id: str
    description: str
