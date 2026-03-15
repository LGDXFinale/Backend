from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RegionPreset:
    name: str
    aliases: tuple[str, ...]
    latitude: float
    longitude: float
    mid_land_reg_id: str
    mid_ta_reg_id: str
    description: str


REGION_PRESETS: tuple[RegionPreset, ...] = (
    RegionPreset(
        name="서울",
        aliases=("서울", "seoul"),
        latitude=37.5665,
        longitude=126.9780,
        mid_land_reg_id="11B00000",
        mid_ta_reg_id="11B10101",
        description="서울 대표 좌표와 수도권 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="인천",
        aliases=("인천", "incheon"),
        latitude=37.4563,
        longitude=126.7052,
        mid_land_reg_id="11B00000",
        mid_ta_reg_id="11B20201",
        description="인천 대표 좌표와 수도권 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="경기",
        aliases=("경기", "경기도", "gyeonggi", "suwon", "수원"),
        latitude=37.2636,
        longitude=127.0286,
        mid_land_reg_id="11B00000",
        mid_ta_reg_id="11B20601",
        description="수원 기준 좌표와 수도권 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="충남",
        aliases=("충남", "충청남도", "대전", "daejeon", "세종", "sejong"),
        latitude=36.3504,
        longitude=127.3845,
        mid_land_reg_id="11C20000",
        mid_ta_reg_id="11C20401",
        description="대전 기준 좌표와 대전·세종·충남 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="충북",
        aliases=("충북", "충청북도", "청주", "cheongju"),
        latitude=36.6424,
        longitude=127.4890,
        mid_land_reg_id="11C10000",
        mid_ta_reg_id="11C10301",
        description="청주 기준 좌표와 충북 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="강원영서",
        aliases=("강원영서", "강원도영서", "춘천", "chuncheon"),
        latitude=37.8813,
        longitude=127.7298,
        mid_land_reg_id="11D10000",
        mid_ta_reg_id="11D10301",
        description="춘천 기준 좌표와 강원영서 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="강원영동",
        aliases=("강원영동", "강원도영동", "강릉", "gangneung"),
        latitude=37.7519,
        longitude=128.8761,
        mid_land_reg_id="11D20000",
        mid_ta_reg_id="11D20501",
        description="강릉 기준 좌표와 강원영동 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="전북",
        aliases=("전북", "전라북도", "전북특별자치도", "전주", "jeonju"),
        latitude=35.8242,
        longitude=127.1480,
        mid_land_reg_id="11F10000",
        mid_ta_reg_id="11F10201",
        description="전주 기준 좌표와 전북 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="전남",
        aliases=("전남", "전라남도", "광주", "gwangju"),
        latitude=35.1595,
        longitude=126.8526,
        mid_land_reg_id="11F20000",
        mid_ta_reg_id="11F20501",
        description="광주 기준 좌표와 광주·전남 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="경북",
        aliases=("경북", "경상북도", "대구", "daegu"),
        latitude=35.8714,
        longitude=128.6014,
        mid_land_reg_id="11H10000",
        mid_ta_reg_id="11H10701",
        description="대구 기준 좌표와 대구·경북 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="포항",
        aliases=("포항", "pohang"),
        latitude=36.0190,
        longitude=129.3435,
        mid_land_reg_id="11H10000",
        mid_ta_reg_id="11H10201",
        description="포항 대표 좌표와 대구·경북 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="안동",
        aliases=("안동", "andong"),
        latitude=36.5684,
        longitude=128.7294,
        mid_land_reg_id="11H10000",
        mid_ta_reg_id="11H10501",
        description="안동 대표 좌표와 대구·경북 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="부산",
        aliases=("부산", "busan"),
        latitude=35.1796,
        longitude=129.0756,
        mid_land_reg_id="11H20000",
        mid_ta_reg_id="11H20201",
        description="부산 대표 좌표와 부산·울산·경남 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="울산",
        aliases=("울산", "ulsan"),
        latitude=35.5384,
        longitude=129.3114,
        mid_land_reg_id="11H20000",
        mid_ta_reg_id="11H20101",
        description="울산 대표 좌표와 부산·울산·경남 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="경남",
        aliases=("경남", "경상남도", "창원", "changwon"),
        latitude=35.2285,
        longitude=128.6811,
        mid_land_reg_id="11H20000",
        mid_ta_reg_id="11H20301",
        description="창원 기준 좌표와 부산·울산·경남 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="제주",
        aliases=("제주", "제주도", "제주시", "jeju"),
        latitude=33.4996,
        longitude=126.5312,
        mid_land_reg_id="11G00000",
        mid_ta_reg_id="11G00201",
        description="제주 대표 좌표와 제주 중기예보 코드를 사용합니다.",
    ),
    RegionPreset(
        name="서귀포",
        aliases=("서귀포", "seogwipo"),
        latitude=33.2541,
        longitude=126.5601,
        mid_land_reg_id="11G00000",
        mid_ta_reg_id="11G00401",
        description="서귀포 대표 좌표와 제주 중기예보 코드를 사용합니다.",
    ),
)

_REGION_INDEX = {
    alias.strip().lower().replace(" ", ""): preset
    for preset in REGION_PRESETS
    for alias in preset.aliases
}


def get_region_presets() -> list[RegionPreset]:
    return list(REGION_PRESETS)


def resolve_region_preset(region_name: str) -> RegionPreset | None:
    normalized = region_name.strip().lower().replace(" ", "")
    return _REGION_INDEX.get(normalized)


def find_nearest_region_preset(latitude: float, longitude: float) -> RegionPreset:
    return min(
        REGION_PRESETS,
        key=lambda preset: _haversine_km(
            latitude,
            longitude,
            preset.latitude,
            preset.longitude,
        ),
    )


def latlon_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
    """Convert WGS84 latitude/longitude to KMA DFS grid coordinates."""

    re = 6371.00877
    grid = 5.0
    slat1 = 30.0
    slat2 = 60.0
    olon = 126.0
    olat = 38.0
    xo = 43.0
    yo = 136.0

    degrad = math.pi / 180.0
    re /= grid
    slat1 *= degrad
    slat2 *= degrad
    olon *= degrad
    olat *= degrad

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + latitude * degrad * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = longitude * degrad - olon

    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi

    theta *= sn

    x = math.floor(ra * math.sin(theta) + xo + 0.5)
    y = math.floor(ro - ra * math.cos(theta) + yo + 0.5)
    return int(x), int(y)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c
