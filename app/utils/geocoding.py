from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode
from urllib.request import urlopen


AddressType = Literal["auto", "road", "parcel"]


@dataclass(frozen=True)
class GeocodedAddress:
    address: str
    latitude: float
    longitude: float
    address_type: str
    refined_text: str | None


class VWorldGeocoderError(RuntimeError):
    """브이월드 지오코딩 처리 중 발생한 오류."""


class VWorldGeocoder:
    GEOCODER_URL = "https://api.vworld.kr/req/address"

    def __init__(self, api_key: str | None = None, timeout: int = 10) -> None:
        self.api_key = api_key or self._load_vworld_api_key()
        self.timeout = timeout

    async def geocode(
        self,
        *,
        address: str,
        address_type: AddressType = "auto",
        refine: bool = True,
    ) -> GeocodedAddress:
        if address_type == "auto":
            candidates: tuple[Literal["road", "parcel"], ...] = ("road", "parcel")
        else:
            candidates = (address_type,)

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return await asyncio.to_thread(
                    self._geocode_sync,
                    address=address,
                    address_type=candidate,
                    refine=refine,
                )
            except VWorldGeocoderError as exc:
                last_error = exc

        raise VWorldGeocoderError(str(last_error) if last_error else "주소 좌표 변환에 실패했습니다.")

    def _geocode_sync(
        self,
        *,
        address: str,
        address_type: Literal["road", "parcel"],
        refine: bool,
    ) -> GeocodedAddress:
        params = {
            "service": "address",
            "request": "getCoord",
            "version": "2.0",
            "format": "json",
            "crs": "EPSG:4326",
            "type": address_type.upper(),
            "address": address,
            "refine": str(refine).lower(),
            "simple": "false",
            "key": self.api_key,
        }
        request_url = f"{self.GEOCODER_URL}?{urlencode(params)}"

        try:
            with urlopen(request_url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise VWorldGeocoderError("브이월드 지오코딩 API 호출에 실패했습니다.") from exc

        response_payload = payload.get("response", {})
        status = response_payload.get("status")
        if status != "OK":
            if status == "NOT_FOUND":
                raise VWorldGeocoderError(f"주소를 찾지 못했습니다: {address}")

            error_text = response_payload.get("error", {}).get("text")
            raise VWorldGeocoderError(error_text or "지오코딩 API 오류가 발생했습니다.")

        result = response_payload.get("result", {})
        point = result.get("point", {})
        refined = response_payload.get("refined", {})

        try:
            longitude = float(point["x"])
            latitude = float(point["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise VWorldGeocoderError("지오코딩 응답에서 좌표를 읽지 못했습니다.") from exc

        return GeocodedAddress(
            address=address,
            latitude=latitude,
            longitude=longitude,
            address_type=address_type,
            refined_text=refined.get("text"),
        )

    @staticmethod
    def _load_vworld_api_key() -> str:
        env_key = os.getenv("VWORLD_API_KEY")
        if env_key:
            return env_key

        for env_path in VWorldGeocoder._candidate_env_paths():
            if not env_path.exists():
                continue

            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                if key.strip() == "VWORLD_API_KEY":
                    value = value.strip().strip("'").strip('"')
                    if value:
                        return value

        raise VWorldGeocoderError("VWORLD_API_KEY 값을 찾을 수 없습니다.")

    @staticmethod
    def _candidate_env_paths() -> list[Path]:
        current = Path(__file__).resolve()
        return [parent / ".env" for parent in current.parents]


async def geocode_address(
    *,
    address: str,
    address_type: AddressType = "auto",
    refine: bool = True,
    api_key: str | None = None,
    timeout: int = 10,
) -> GeocodedAddress:
    geocoder = VWorldGeocoder(api_key=api_key, timeout=timeout)
    return await geocoder.geocode(
        address=address,
        address_type=address_type,
        refine=refine,
    )
