from __future__ import annotations

from dataclasses import dataclass


DEFAULT_DEMO_SCENARIO = "single_household"


@dataclass(frozen=True)
class DemoScenarioDefaults:
    key: str
    label: str
    summary: str
    member_id: str
    washer_id: str
    wash_status_id: str
    washer_capacity_kg: float
    household_size: int
    region: str
    city: str
    current_load_kg: float
    sensor_load_kg: float
    weight_increase_kg: float
    hours_since_last_wash: float
    urgent_clothing_count: int
    load_variation_kg: float
    cycle_elapsed_minutes: int
    base_cycle_minutes: int
    final_spin_rpm: int
    dry_laundry_weight_kg: float
    has_delicate_items: bool
    needs_fast_dry: bool
    has_outdoor_space: bool
    has_dryer: bool
    odor_sensitive: bool
    indoor_humidity: int
    indoor_temperature: float
    airflow_level: int
    dehumidifier_on: bool


DEMO_SCENARIOS: dict[str, DemoScenarioDefaults] = {
    "single_household": DemoScenarioDefaults(
        key="single_household",
        label="바쁜 1인 가구",
        summary=(
            "세탁 주기가 조금 길어져 빨래가 한 번에 모였고, 급하게 입어야 하는 옷이 있어 "
            "빠른 세탁과 실내 중심 건조가 필요한 1인 가구 시나리오입니다."
        ),
        member_id="member-single-001",
        washer_id="washer-single-001",
        wash_status_id="wash-status-single-001",
        washer_capacity_kg=9.0,
        household_size=1,
        region="seoul",
        city="Seoul",
        current_load_kg=3.1,
        sensor_load_kg=3.1,
        weight_increase_kg=0.8,
        hours_since_last_wash=60.0,
        urgent_clothing_count=1,
        load_variation_kg=0.2,
        cycle_elapsed_minutes=28,
        base_cycle_minutes=68,
        final_spin_rpm=1000,
        dry_laundry_weight_kg=3.0,
        has_delicate_items=False,
        needs_fast_dry=True,
        has_outdoor_space=False,
        has_dryer=False,
        odor_sensitive=False,
        indoor_humidity=58,
        indoor_temperature=24.0,
        airflow_level=55,
        dehumidifier_on=True,
    ),
    "family4_household": DemoScenarioDefaults(
        key="family4_household",
        label="바쁜 4인 가구",
        summary=(
            "가족 빨래가 빠르게 많이 쌓이고 급하게 세탁해야 하는 옷도 있어, "
            "세탁과 건조를 모두 빠르게 처리해야 하는 4인 가구 시나리오입니다."
        ),
        member_id="member-family4-001",
        washer_id="washer-family4-001",
        wash_status_id="wash-status-family4-001",
        washer_capacity_kg=14.0,
        household_size=4,
        region="seoul",
        city="Seoul",
        current_load_kg=8.6,
        sensor_load_kg=8.8,
        weight_increase_kg=2.4,
        hours_since_last_wash=36.0,
        urgent_clothing_count=3,
        load_variation_kg=0.6,
        cycle_elapsed_minutes=42,
        base_cycle_minutes=88,
        final_spin_rpm=1000,
        dry_laundry_weight_kg=7.8,
        has_delicate_items=False,
        needs_fast_dry=True,
        has_outdoor_space=False,
        has_dryer=True,
        odor_sensitive=True,
        indoor_humidity=64,
        indoor_temperature=23.0,
        airflow_level=35,
        dehumidifier_on=False,
    ),
}


DEMO_SCENARIO_ALIASES = {
    "single": "single_household",
    "1": "single_household",
    "1p": "single_household",
    "1person": "single_household",
    "1인가구": "single_household",
    "family4": "family4_household",
    "family": "family4_household",
    "4": "family4_household",
    "4p": "family4_household",
    "4person": "family4_household",
    "4인가구": "family4_household",
}


def get_demo_scenario(scenario: str | None = None) -> DemoScenarioDefaults:
    key = (scenario or DEFAULT_DEMO_SCENARIO).strip().lower()
    resolved_key = DEMO_SCENARIO_ALIASES.get(key, key)
    return DEMO_SCENARIOS.get(resolved_key, DEMO_SCENARIOS[DEFAULT_DEMO_SCENARIO])


_default = get_demo_scenario()

DEMO_MEMBER_ID = _default.member_id
DEMO_WASHER_ID = _default.washer_id
DEMO_WASH_STATUS_ID = _default.wash_status_id

DEMO_WASHER_CAPACITY_KG = _default.washer_capacity_kg
DEMO_HOUSEHOLD_SIZE = _default.household_size
DEMO_REGION = _default.region
DEMO_CITY = _default.city

DEMO_CURRENT_LOAD_KG = _default.current_load_kg
DEMO_SENSOR_LOAD_KG = _default.sensor_load_kg
DEMO_WEIGHT_INCREASE_KG = _default.weight_increase_kg

DEMO_HOURS_SINCE_LAST_WASH = _default.hours_since_last_wash
DEMO_URGENT_CLOTHING_COUNT = _default.urgent_clothing_count

DEMO_LOAD_VARIATION_KG = _default.load_variation_kg
DEMO_CYCLE_ELAPSED_MINUTES = _default.cycle_elapsed_minutes
DEMO_BASE_CYCLE_MINUTES = _default.base_cycle_minutes
DEMO_FINAL_SPIN_RPM = _default.final_spin_rpm

DEMO_DRY_LAUNDRY_WEIGHT_KG = _default.dry_laundry_weight_kg
DEMO_HAS_DELICATE_ITEMS = _default.has_delicate_items
DEMO_NEEDS_FAST_DRY = _default.needs_fast_dry
DEMO_HAS_OUTDOOR_SPACE = _default.has_outdoor_space
DEMO_HAS_DRYER = _default.has_dryer
DEMO_ODOR_SENSITIVE = _default.odor_sensitive
DEMO_INDOOR_HUMIDITY = _default.indoor_humidity
DEMO_INDOOR_TEMPERATURE = _default.indoor_temperature
DEMO_AIRFLOW_LEVEL = _default.airflow_level
DEMO_DEHUMIDIFIER_ON = _default.dehumidifier_on
