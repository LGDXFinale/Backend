"""Shared utilities used across multiple feature domains."""

from .air_quality import (
    AirKoreaClient,
    AirQualityError,
    AirQualityObservation,
    get_current_air_quality,
)
from .geocoding import (
    GeocodedAddress,
    VWorldGeocoder,
    VWorldGeocoderError,
    geocode_address,
)
from .weather_regions import (
    RegionPreset,
    find_nearest_region_preset,
    get_region_presets,
    latlon_to_grid,
    resolve_region_preset,
)
from .weather_forecast import (
    PublicDataWeatherClient,
    PublicDataWeatherError,
    get_weekly_weather,
)

__all__ = [
    "AirKoreaClient",
    "AirQualityError",
    "AirQualityObservation",
    "GeocodedAddress",
    "PublicDataWeatherClient",
    "PublicDataWeatherError",
    "RegionPreset",
    "VWorldGeocoder",
    "VWorldGeocoderError",
    "find_nearest_region_preset",
    "geocode_address",
    "get_current_air_quality",
    "get_region_presets",
    "get_weekly_weather",
    "latlon_to_grid",
    "resolve_region_preset",
]
