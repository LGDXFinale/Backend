import os
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/dry-recommendation", tags=["dry-recommendation"])


def get_weather_data():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    city = "Seoul"
    url = "https://api.openweathermap.org/data/2.5/weather"

    if not api_key:
        # 테스트용 더미값
        return {
            "is_raining": False,
            "humidity": 55,
            "temperature": 22
        }

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="외부 날씨 API 호출에 실패했습니다.")

    data = response.json()

    weather_main = data["weather"][0]["main"]
    humidity = data["main"]["humidity"]
    temperature = data["main"]["temp"]

    is_raining = weather_main in ["Rain", "Drizzle", "Thunderstorm"]

    return {
        "is_raining": is_raining,
        "humidity": humidity,
        "temperature": temperature
    }


@router.get("/recommend")
def get_dry_recommendation():
    weather_data = get_weather_data()

    is_raining = weather_data["is_raining"]
    humidity = weather_data["humidity"]
    temperature = weather_data["temperature"]

    # 1 = 실내건조, 2 = 실외건조, 3 = 건조기
    if is_raining:
        dry_rec_method = 3
        dry_rec_time = 60
        reason = "비가 와서 건조기를 추천합니다."
    elif humidity >= 80:
        dry_rec_method = 3
        dry_rec_time = 70
        reason = "습도가 높아 건조기를 추천합니다."
    elif temperature >= 20 and humidity < 60:
        dry_rec_method = 2
        dry_rec_time = 120
        reason = "기온이 적절하고 습도가 낮아 실외건조를 추천합니다."
    else:
        dry_rec_method = 1
        dry_rec_time = 180
        reason = "현재 날씨 기준으로 실내건조를 추천합니다."

    method_map = {
        1: "실내건조",
        2: "실외건조",
        3: "건조기"
    }

    return {
        "dry_rec_id": "DR001",
        "dry_rec_time": dry_rec_time,
        "dry_rec_method": dry_rec_method,
        "dry_rec_method_name": method_map.get(dry_rec_method, "알 수 없음"),
        "reason": reason,
        "weather_info": {
            "is_raining": is_raining,
            "humidity": humidity,
            "temperature": temperature
        }
    }