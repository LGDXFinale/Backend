from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


class PublicDataWeatherError(RuntimeError):
    """Raised when the public weather API cannot be read or parsed."""


class PublicDataWeatherClient:
    """Fetches and merges 7-day forecasts from the public weather APIs."""

    VILAGE_FCST_URL = (
        "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    )
    MID_LAND_FCST_URL = (
        "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"
    )
    MID_TA_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
    VILAGE_BASE_TIMES = ("0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300")
    MID_BASE_TIMES = ("0600", "1800")
    PUBLISH_BUFFER_MINUTES = 10

    def __init__(self, service_key: str | None = None, timeout: int = 10) -> None:
        self.service_key = service_key or self._load_public_data_api_key()
        self.timeout = timeout

    async def get_weekly_weather(
        self,
        *,
        nx: int,
        ny: int,
        mid_land_reg_id: str,
        mid_ta_reg_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Return a merged 7-day forecast.

        `nx` and `ny` are the short-term village forecast grid coordinates.
        `mid_land_reg_id` and `mid_ta_reg_id` are the mid-term regional forecast codes.
        """

        now_kst = self._as_kst(now)
        village_base = self._select_base_datetime(now_kst, self.VILAGE_BASE_TIMES)
        mid_base = self._select_base_datetime(now_kst, self.MID_BASE_TIMES)

        village_task = asyncio.create_task(
            self._request_items(
                self.VILAGE_FCST_URL,
                {
                    "serviceKey": self.service_key,
                    "pageNo": 1,
                    "numOfRows": 1000,
                    "dataType": "JSON",
                    "base_date": village_base.strftime("%Y%m%d"),
                    "base_time": village_base.strftime("%H%M"),
                    "nx": nx,
                    "ny": ny,
                },
            )
        )
        mid_land_task = asyncio.create_task(
            self._request_items(
                self.MID_LAND_FCST_URL,
                {
                    "serviceKey": self.service_key,
                    "pageNo": 1,
                    "numOfRows": 10,
                    "dataType": "JSON",
                    "regId": mid_land_reg_id,
                    "tmFc": mid_base.strftime("%Y%m%d%H%M"),
                },
            )
        )
        mid_ta_task = asyncio.create_task(
            self._request_items(
                self.MID_TA_URL,
                {
                    "serviceKey": self.service_key,
                    "pageNo": 1,
                    "numOfRows": 10,
                    "dataType": "JSON",
                    "regId": mid_ta_reg_id,
                    "tmFc": mid_base.strftime("%Y%m%d%H%M"),
                },
            )
        )

        village_items, mid_land_items, mid_ta_items = await asyncio.gather(
            village_task, mid_land_task, mid_ta_task
        )

        short_term_days = self._parse_village_forecast(village_items, now_kst.date())
        mid_term_days = self._parse_mid_forecast(
            mid_land_items, mid_ta_items, mid_base.date(), now_kst.date()
        )
        merged_days = self._merge_days(short_term_days, mid_term_days, now_kst.date())

        return {
            "generated_at": now_kst.isoformat(),
            "location": {
                "nx": nx,
                "ny": ny,
                "mid_land_reg_id": mid_land_reg_id,
                "mid_ta_reg_id": mid_ta_reg_id,
            },
            "sources": {
                "vilage_base_datetime": village_base.isoformat(),
                "mid_base_datetime": mid_base.isoformat(),
            },
            "days": merged_days,
        }

    async def _request_items(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._request_items_sync, url, params)

    def _request_items_sync(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        request_url = f"{url}?{urlencode(params)}"

        try:
            with urlopen(request_url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise PublicDataWeatherError(f"공공데이터 API 호출에 실패했습니다: {url}") from exc

        header = payload.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            message = header.get("resultMsg", "Unknown error")
            raise PublicDataWeatherError(f"공공데이터 API 오류: {message}")

        items = payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items

        raise PublicDataWeatherError("공공데이터 API 응답 형식이 예상과 다릅니다.")

    def _parse_village_forecast(
        self, items: list[dict[str, Any]], today: date
    ) -> list[dict[str, Any]]:
        target_dates = {today + timedelta(days=offset) for offset in range(3)}
        grouped: dict[date, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))

        for item in items:
            fcst_date = self._parse_compact_date(item.get("fcstDate"))
            if fcst_date not in target_dates:
                continue

            category = item.get("category")
            value = item.get("fcstValue")
            if category:
                grouped[fcst_date][category].append(value)

        results: list[dict[str, Any]] = []
        for target_date in sorted(target_dates):
            if target_date not in grouped:
                continue

            categories = grouped[target_date]
            pty_values = [self._to_int(value) for value in categories.get("PTY", [])]
            pty_values = [value for value in pty_values if value is not None and value > 0]
            sky_values = [self._to_int(value) for value in categories.get("SKY", [])]
            sky_values = [value for value in sky_values if value is not None]
            pop_values = [self._to_int(value) for value in categories.get("POP", [])]
            pop_values = [value for value in pop_values if value is not None]
            reh_values = [self._to_int(value) for value in categories.get("REH", [])]
            reh_values = [value for value in reh_values if value is not None]

            precipitation_summary = self._describe_precipitation_codes(pty_values)
            sky = self._describe_sky(max(sky_values)) if sky_values else None

            results.append(
                {
                    "date": target_date.isoformat(),
                    "source": "vilage_fcst",
                    "min_temp": self._first_number(categories.get("TMN", [])),
                    "max_temp": self._first_number(categories.get("TMX", [])),
                    "precipitation_probability": max(pop_values) if pop_values else None,
                    "relative_humidity": max(reh_values) if reh_values else None,
                    "feels_like_temp": self._calculate_apparent_temperature(
                        temperature=self._first_number(categories.get("TMP", [])),
                        relative_humidity=max(reh_values) if reh_values else None,
                        wind_speed=self._max_number(categories.get("WSD", [])),
                    ),
                    "summary": precipitation_summary or sky,
                }
            )

        return results

    def _parse_mid_forecast(
        self,
        land_items: list[dict[str, Any]],
        ta_items: list[dict[str, Any]],
        base_date: date,
        today: date,
    ) -> list[dict[str, Any]]:
        if not land_items or not ta_items:
            return []

        land = land_items[0]
        ta = ta_items[0]
        results: list[dict[str, Any]] = []

        for offset in range(3, 8):
            target_date = base_date + timedelta(days=offset)
            if target_date < today:
                continue

            am_summary = land.get(f"wf{offset}Am")
            pm_summary = land.get(f"wf{offset}Pm")
            rain_am = self._to_int(land.get(f"rnSt{offset}Am"))
            rain_pm = self._to_int(land.get(f"rnSt{offset}Pm"))
            precipitation_probability = max(
                [value for value in (rain_am, rain_pm) if value is not None],
                default=None,
            )

            summary = self._merge_summaries(am_summary, pm_summary)
            if not summary:
                continue

            results.append(
                {
                    "date": target_date.isoformat(),
                    "source": "mid_fcst",
                    "min_temp": self._to_float(ta.get(f"taMin{offset}")),
                    "max_temp": self._to_float(ta.get(f"taMax{offset}")),
                    "precipitation_probability": precipitation_probability,
                    "relative_humidity": None,
                    "feels_like_temp": None,
                    "summary": summary,
                }
            )

        return results

    def _merge_days(
        self,
        short_term_days: list[dict[str, Any]],
        mid_term_days: list[dict[str, Any]],
        today: date,
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}

        for day in short_term_days + mid_term_days:
            day_date = day["date"]
            if day_date not in merged:
                merged[day_date] = day

        ordered_dates = sorted(
            day_date for day_date in merged if self._parse_iso_date(day_date) >= today
        )
        return [merged[day_date] for day_date in ordered_dates[:7]]

    @staticmethod
    def _select_base_datetime(now_kst: datetime, schedule: tuple[str, ...]) -> datetime:
        effective_now = now_kst - timedelta(minutes=PublicDataWeatherClient.PUBLISH_BUFFER_MINUTES)
        current_hhmm = effective_now.strftime("%H%M")

        for hhmm in reversed(schedule):
            if current_hhmm >= hhmm:
                return datetime.combine(
                    effective_now.date(),
                    time(hour=int(hhmm[:2]), minute=int(hhmm[2:])),
                    tzinfo=KST,
                )

        previous_day = effective_now.date() - timedelta(days=1)
        fallback_hhmm = schedule[-1]
        return datetime.combine(
            previous_day,
            time(hour=int(fallback_hhmm[:2]), minute=int(fallback_hhmm[2:])),
            tzinfo=KST,
        )

    @staticmethod
    def _as_kst(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(KST)
        if value.tzinfo is None:
            return value.replace(tzinfo=KST)
        return value.astimezone(KST)

    @staticmethod
    def _parse_compact_date(value: Any) -> date | None:
        if not value:
            return None
        return datetime.strptime(str(value), "%Y%m%d").date()

    @staticmethod
    def _parse_iso_date(value: str) -> date:
        return date.fromisoformat(value)

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None

    def _first_number(self, values: list[Any]) -> float | None:
        if not values:
            return None
        return self._to_float(values[0])

    def _max_number(self, values: list[Any]) -> float | None:
        if not values:
            return None
        numbers = [self._to_float(value) for value in values]
        numbers = [value for value in numbers if value is not None]
        if not numbers:
            return None
        return max(numbers)

    def _calculate_apparent_temperature(
        self,
        *,
        temperature: float | None,
        relative_humidity: int | None,
        wind_speed: float | None,
    ) -> float | None:
        if temperature is None or relative_humidity is None or wind_speed is None:
            return None

        # 기온, 상대습도, 풍속으로 체감온도를 근사 계산한다.
        vapor_pressure = (relative_humidity / 100) * 6.105 * pow(
            2.718281828,
            (17.27 * temperature) / (237.7 + temperature),
        )
        apparent = temperature + 0.33 * vapor_pressure - 0.70 * wind_speed - 4.0
        return round(apparent, 1)

    @staticmethod
    def _describe_sky(code: int) -> str | None:
        mapping = {
            1: "맑음",
            3: "구름많음",
            4: "흐림",
        }
        return mapping.get(code)

    @staticmethod
    def _describe_precipitation_codes(codes: list[int]) -> str | None:
        mapping = {
            1: "비",
            2: "비/눈",
            3: "눈",
            4: "소나기",
        }
        names = [mapping[code] for code in sorted(set(codes)) if code in mapping]
        if not names:
            return None
        return "/".join(names)

    @staticmethod
    def _merge_summaries(am_summary: Any, pm_summary: Any) -> str | None:
        am = str(am_summary).strip() if am_summary else ""
        pm = str(pm_summary).strip() if pm_summary else ""

        if am and pm and am != pm:
            return f"오전 {am}, 오후 {pm}"
        return am or pm or None

    @staticmethod
    def _load_public_data_api_key() -> str:
        env_key = os.getenv("PUBLIC_DATA_API_KEY")
        if env_key:
            return env_key

        for env_path in PublicDataWeatherClient._candidate_env_paths():
            if not env_path.exists():
                continue

            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                if key.strip() == "PUBLIC_DATA_API_KEY":
                    value = value.strip().strip("'").strip('"')
                    if value:
                        return value

        raise PublicDataWeatherError("PUBLIC_DATA_API_KEY 값을 찾을 수 없습니다.")

    @staticmethod
    def _candidate_env_paths() -> list[Path]:
        current = Path(__file__).resolve()
        candidates: list[Path] = []
        for parent in current.parents:
            candidates.append(parent / ".env")
        return candidates


async def get_weekly_weather(
    *,
    nx: int,
    ny: int,
    mid_land_reg_id: str,
    mid_ta_reg_id: str,
    now: datetime | None = None,
    service_key: str | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    """Convenience wrapper for direct use inside a FastAPI route or service."""

    client = PublicDataWeatherClient(service_key=service_key, timeout=timeout)
    return await client.get_weekly_weather(
        nx=nx,
        ny=ny,
        mid_land_reg_id=mid_land_reg_id,
        mid_ta_reg_id=mid_ta_reg_id,
        now=now,
    )
