from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


class AirQualityError(RuntimeError):
    """Raised when the Air Korea API cannot be read or parsed."""


@dataclass(frozen=True)
class AirQualityObservation:
    station_name: str
    station_address: str | None
    measured_at: str | None
    pm10: int | None
    pm10_grade: str | None
    pm25: int | None
    pm25_grade: str | None
    source: str = "air_korea"


class AirKoreaClient:
    CITY_AIR_QUALITY_URL = (
        "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    )

    def __init__(self, service_key: str | None = None, timeout: int = 10) -> None:
        self.service_key = service_key or self._load_air_korea_api_key()
        self.timeout = timeout

    async def get_current_air_quality(
        self,
        *,
        latitude: float,
        longitude: float,
        address_hint: str,
    ) -> AirQualityObservation | None:
        return await asyncio.to_thread(
            self._get_current_air_quality_sync,
            latitude=latitude,
            longitude=longitude,
            address_hint=address_hint,
        )

    def _get_current_air_quality_sync(
        self,
        *,
        latitude: float,
        longitude: float,
        address_hint: str,
    ) -> AirQualityObservation | None:
        sido_name = self._normalize_sido_name(address_hint)
        if not sido_name:
            return None

        measures = self._request_items(
            self.CITY_AIR_QUALITY_URL,
            {
                "serviceKey": self.service_key,
                "returnType": "json",
                "numOfRows": 100,
                "pageNo": 1,
                "sidoName": sido_name,
                "ver": "1.0",
            },
        )
        if not measures:
            return None

        measure = max(
            measures,
            key=lambda item: self._city_measure_score(
                item=item,
                latitude=latitude,
                longitude=longitude,
                address_hint=address_hint,
            ),
        )
        station_name = str(measure.get("stationName", "")).strip()
        if not station_name:
            return None

        return AirQualityObservation(
            station_name=station_name,
            station_address=sido_name,
            measured_at=measure.get("dataTime"),
            pm10=self._to_int(measure.get("pm10Value")),
            pm10_grade=self._describe_air_grade(measure.get("pm10Grade")),
            pm25=self._to_int(measure.get("pm25Value")),
            pm25_grade=self._describe_air_grade(measure.get("pm25Grade")),
        )

    def _city_measure_score(
        self,
        *,
        item: dict[str, Any],
        latitude: float,
        longitude: float,
        address_hint: str,
    ) -> float:
        del latitude, longitude

        score = 0.0
        station_name = str(item.get("stationName", "")).strip()
        mang_name = str(item.get("mangName", "")).strip()

        if "도시대기" in mang_name:
            score += 20
        elif "도로변대기" in mang_name:
            score += 12

        for token in [token for token in address_hint.split() if token]:
            if token in station_name:
                score += 15

        return score

    def _request_items(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        request_url = f"{url}?{urlencode(params)}"

        try:
            with urlopen(request_url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise AirQualityError(f"에어코리아 API 호출에 실패했습니다: {url}") from exc

        header = payload.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            message = header.get("resultMsg", "Unknown error")
            raise AirQualityError(f"에어코리아 API 오류: {message}")

        items = payload.get("response", {}).get("body", {}).get("items", [])
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items
        return []

    def _normalize_sido_name(self, address_hint: str) -> str | None:
        tokens = [token for token in address_hint.split() if token]
        if not tokens:
            return None

        mapping = {
            "서울": "서울",
            "서울특별시": "서울",
            "부산": "부산",
            "부산광역시": "부산",
            "대구": "대구",
            "대구광역시": "대구",
            "인천": "인천",
            "인천광역시": "인천",
            "광주": "광주",
            "광주광역시": "광주",
            "대전": "대전",
            "대전광역시": "대전",
            "울산": "울산",
            "울산광역시": "울산",
            "세종": "세종",
            "세종특별자치시": "세종",
            "경기": "경기",
            "경기도": "경기",
            "강원": "강원",
            "강원도": "강원",
            "강원특별자치도": "강원",
            "충북": "충북",
            "충청북도": "충북",
            "충남": "충남",
            "충청남도": "충남",
            "전북": "전북",
            "전북특별자치도": "전북",
            "전라북도": "전북",
            "전남": "전남",
            "전라남도": "전남",
            "경북": "경북",
            "경상북도": "경북",
            "경남": "경남",
            "경상남도": "경남",
            "제주": "제주",
            "제주특별자치도": "제주",
        }
        return mapping.get(tokens[0])

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            text = str(value).strip()
            if text in {"", "-", "통신장애"}:
                return None
            return int(float(text))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _describe_air_grade(value: Any) -> str | None:
        mapping = {
            "1": "좋음",
            "2": "보통",
            "3": "나쁨",
            "4": "매우나쁨",
        }
        text = str(value).strip()
        return mapping.get(text) or (text if text else None)

    @staticmethod
    def _load_air_korea_api_key() -> str:
        env_key = os.getenv("PUBLIC_DATA_API_KEY")
        if env_key:
            return env_key

        for env_path in AirKoreaClient._candidate_env_paths():
            if not env_path.exists():
                continue

            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                normalized_key = key.strip()
                if normalized_key != "PUBLIC_DATA_API_KEY":
                    continue

                value = value.strip().strip("'").strip('"')
                if value:
                    return value

        raise AirQualityError("PUBLIC_DATA_API_KEY 값을 찾을 수 없습니다.")

    @staticmethod
    def _candidate_env_paths() -> list[Path]:
        current = Path(__file__).resolve()
        return [parent / ".env" for parent in current.parents]


async def get_current_air_quality(
    *,
    latitude: float,
    longitude: float,
    address_hint: str,
    service_key: str | None = None,
    timeout: int = 10,
) -> AirQualityObservation | None:
    client = AirKoreaClient(service_key=service_key, timeout=timeout)
    return await client.get_current_air_quality(
        latitude=latitude,
        longitude=longitude,
        address_hint=address_hint,
    )
