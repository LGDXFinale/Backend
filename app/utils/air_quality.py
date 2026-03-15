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
    """에어코리아 API 처리 중 발생한 오류."""


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
    STATION_INFO_URL = "https://apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getMsrstnList"
    REALTIME_AIR_QUALITY_URL = (
        "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
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
        stations = self._get_station_candidates(address_hint)
        if not stations:
            return None

        nearest_station = max(
            stations,
            key=lambda item: self._station_score(
                item=item,
                latitude=latitude,
                longitude=longitude,
                address_hint=address_hint,
            ),
        )
        station_name = nearest_station.get("stationName")
        if not station_name:
            return None

        measures = self._request_items(
            self.REALTIME_AIR_QUALITY_URL,
            {
                "serviceKey": self.service_key,
                "returnType": "json",
                "numOfRows": 10,
                "pageNo": 1,
                "stationName": station_name,
                "dataTerm": "DAILY",
                "ver": "1.4",
            },
        )
        if not measures:
            return None

        measure = measures[0]
        return AirQualityObservation(
            station_name=station_name,
            station_address=nearest_station.get("addr"),
            measured_at=measure.get("dataTime"),
            pm10=self._to_int(measure.get("pm10Value")),
            pm10_grade=self._describe_air_grade(measure.get("pm10Grade")),
            pm25=self._to_int(measure.get("pm25Value")),
            pm25_grade=self._describe_air_grade(measure.get("pm25Grade")),
        )

    def _get_station_candidates(self, address_hint: str) -> list[dict[str, Any]]:
        seen: set[tuple[str, str]] = set()
        candidates: list[dict[str, Any]] = []

        for addr_query in self._build_address_queries(address_hint):
            stations = self._request_items(
                self.STATION_INFO_URL,
                {
                    "serviceKey": self.service_key,
                    "returnType": "json",
                    "numOfRows": 100,
                    "pageNo": 1,
                    "addr": addr_query,
                },
            )

            for station in stations:
                key = (
                    str(station.get("stationName", "")).strip(),
                    str(station.get("addr", "")).strip(),
                )
                if key in seen:
                    continue

                seen.add(key)
                candidates.append(station)

            if candidates:
                # 좁은 주소에서 이미 후보를 찾았으면 더 넓은 검색은 생략한다.
                break

        return candidates

    def _build_address_queries(self, address_hint: str) -> list[str]:
        tokens = [token for token in address_hint.split() if token]
        if not tokens:
            return [address_hint]

        queries: list[str] = []
        for length in range(min(len(tokens), 3), 0, -1):
            query = " ".join(tokens[:length])
            if query not in queries:
                queries.append(query)

        if address_hint not in queries:
            queries.insert(0, address_hint)

        return queries

    def _station_score(
        self,
        *,
        item: dict[str, Any],
        latitude: float,
        longitude: float,
        address_hint: str,
    ) -> float:
        score = 0.0
        station_name = str(item.get("stationName", "")).strip()
        station_addr = str(item.get("addr", "")).strip()
        mang_name = str(item.get("mangName", "")).strip()
        station_longitude = self._to_float(item.get("dmX"))
        station_latitude = self._to_float(item.get("dmY"))
        distance_sq = self._distance_sq(
            latitude,
            longitude,
            station_latitude,
            station_longitude,
        )

        # 거리 우선으로 점수를 주고, 주소 일치와 측정망 특성을 보정 점수로 더한다.
        if distance_sq != float("inf"):
            score += 1000 / (1 + distance_sq * 10000)

        if "도시대기" in mang_name:
            score += 20
        elif "도로변대기" in mang_name:
            score += 12

        for token in [token for token in address_hint.split() if token]:
            if token in station_addr:
                score += 8
            if token in station_name:
                score += 10

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

    @staticmethod
    def _distance_sq(
        lat1: float,
        lon1: float,
        lat2: float | None,
        lon2: float | None,
    ) -> float:
        if lat2 is None or lon2 is None:
            return float("inf")
        return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None

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
