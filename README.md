# Backend

FastAPI 기반 세탁 추천 백엔드입니다.

현재 구현된 주요 기능:

- 주간 날씨 조회
- 세탁 솔루션 맞춤 제안

## 환경 변수

`.env` 파일에서 아래 값을 사용할 수 있습니다.

- `PUBLIC_DATA_API_KEY`: 기상청 공공데이터 API 키
- `VWORLD_API_KEY`: 브이월드 주소 지오코딩 API 키

참고:

- 에어코리아 조회도 현재는 `PUBLIC_DATA_API_KEY`를 그대로 사용합니다.

## 명세서 보는 방법

서버를 실행한 뒤 브라우저에서 아래 주소로 접속하면 API 명세서를 볼 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

여기는 FastAPI가 자동으로 만들어주는 Swagger UI 화면입니다.

처음 보는 사람 기준으로는 이렇게 보면 됩니다.

- 각 줄이 하나의 API입니다.
- `GET`, `POST` 같은 메서드와 URL 경로를 확인할 수 있습니다.
- 펼쳐보면 필요한 파라미터와 요청 바디 형식을 볼 수 있습니다.
- `Try it out` 버튼을 누르면 브라우저에서 바로 테스트할 수 있습니다.
- `Execute`를 누르면 실제 요청이 보내지고 응답 본문도 바로 확인할 수 있습니다.

JSON 형태의 원본 명세가 필요하면 아래 주소를 사용하면 됩니다.

```text
http://127.0.0.1:8000/openapi.json
```

브라우저가 아니라 터미널에서 확인하고 싶다면 아래처럼 테스트할 수 있습니다.

```bash
curl.exe "http://127.0.0.1:8000/openapi.json"
```

## 실행 방법

프로젝트 루트에서 아래 명령어로 실행합니다.

```bash
uvicorn app.main:app --reload
```

대안으로 아래 명령도 사용할 수 있습니다.

```bash
python -m app.main
```

주의:

- `python app/main.py`처럼 파일을 직접 실행하면 `ModuleNotFoundError: No module named 'app'`가 발생할 수 있습니다.
- 이 프로젝트는 `app` 패키지 기준 import 경로를 사용하므로, 모듈 방식 실행이 안전합니다.

## 주요 엔드포인트

- `GET /health`
- `GET /`
- `GET /api/laundry-timing/weather/regions`
- `GET /api/laundry-timing/weather/weekly`
- `POST /api/fabric-damage/solution`

## curl 테스트

PowerShell에서는 `curl` 대신 `curl.exe` 사용을 권장합니다.

### 기본 상태 확인

```bash
curl.exe "http://127.0.0.1:8000/health"
```

```bash
curl.exe "http://127.0.0.1:8000/"
```

### 날씨 지역 프리셋 조회

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/regions"
```

### 주간 날씨 조회

지역 프리셋 사용:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?region=seoul"
```

설명:

- `region=seoul` 같은 값은 편의를 위한 대표 지역 프리셋입니다.
- 실제 서비스에서 `OO동`, `OO읍`, `OO면`처럼 더 구체적인 위치를 반영하려면 `latitude`, `longitude`를 직접 넘기는 방식이 가장 정확합니다.
- 즉, 프리셋은 빠른 테스트용이고, 세밀한 생활권 날씨는 좌표 기반 호출이 권장됩니다.

위경도 직접 사용:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?latitude=37.5665&longitude=126.9780&mid_land_reg_id=11B00000&mid_ta_reg_id=11B10101"
```

예시:

- 사용자의 GPS 좌표를 이미 알고 있으면 그 값을 그대로 `latitude`, `longitude`에 넣으면 됩니다.
- 주소를 받는 경우에는 이후 단계에서 주소를 좌표로 바꾸는 지오코딩 API를 연결하면 `OO동`, `OO읍` 단위까지 자연스럽게 확장할 수 있습니다.

주소 직접 사용:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?address=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%20%EA%B0%95%EB%82%A8%EA%B5%AC%20%EC%97%AD%EC%82%BC%EB%8F%99&address_type=parcel"
```

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?address=%EA%B2%BD%EA%B8%B0%EB%8F%84%20%EC%96%91%ED%8F%89%EA%B5%B0%20%EC%96%91%EC%84%9C%EB%A9%B4&address_type=parcel"
```

주소 자동 판별 사용:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?address=%EC%84%9C%EC%9A%B8%20%EA%B0%95%EB%82%A8%EA%B5%AC%20%EC%97%AD%EC%82%BC%EB%8F%99&address_type=auto"
```

좌표 직접 입력 후 대기질까지 함께 확인:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?latitude=37.5001&longitude=127.0364&mid_land_reg_id=11B00000&mid_ta_reg_id=11B10101"
```

격자 좌표와 예보 코드를 직접 사용:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?nx=60&ny=127&mid_land_reg_id=11B00000&mid_ta_reg_id=11B10101"
```

잘못된 주소 타입 확인:

```bash
curl.exe "http://127.0.0.1:8000/api/laundry-timing/weather/weekly?address=%EC%84%9C%EC%9A%B8%20%EA%B0%95%EB%82%A8%EA%B5%AC%20%EC%97%AD%EC%82%BC%EB%8F%99&address_type=bad"
```

주의:

- `/api/laundry-timing/weather/weekly`는 실제 공공데이터 API를 호출합니다.
- `address`를 사용하는 경우 브이월드 지오코딩 API도 함께 호출합니다.
- 현재 응답에는 `days` 외에 `current_air_quality`가 포함될 수 있습니다.
- `current_air_quality`는 가장 가까운 대기 측정소의 현재 미세먼지/초미세먼지 측정값입니다.
- 에어코리아 호출이 실패하면 전체 요청이 실패하지 않고 `current_air_quality`는 `null`, `current_air_quality_error`에 오류 문자열이 들어갑니다.
- `PUBLIC_DATA_API_KEY`가 `.env`에 있어야 합니다.
- `VWORLD_API_KEY`가 없으면 주소 기반 조회는 동작하지 않습니다.
- `일조량`은 현재 제외했습니다.
- `relative_humidity`는 단기예보 기준으로 채워지며, 중기예보 구간은 `null`일 수 있습니다.
- `feels_like_temp`는 기온, 습도, 풍속 기반 계산값이라 중기예보 구간은 `null`일 수 있습니다.
- `summary`에는 하늘 상태 또는 비/눈 같은 핵심 예보 요약이 들어갑니다.

현재 응답 주요 필드:

- `days[].relative_humidity`: 단기예보 상대습도
- `days[].feels_like_temp`: 기온, 습도, 풍속 기반 계산 체감온도
- `days[].summary`: 하늘 상태 또는 강수 형태를 포함한 요약
- `current_air_quality.pm10`: 현재 미세먼지(PM10)
- `current_air_quality.pm25`: 현재 초미세먼지(PM2.5)
- `current_air_quality.station_name`: 선택된 측정소 이름
- `current_air_quality_error`: 대기질 조회 실패 시 오류 메시지

### 세탁 솔루션 맞춤 제안

기본 테스트:

```bash
curl.exe -X POST "http://127.0.0.1:8000/api/fabric-damage/solution" -H "Content-Type: application/json" -d "{\"member_id\":\"member-001\",\"washer_id\":\"washer-001\",\"wash_id\":\"wash-001\",\"washer_capacity_kg\":12,\"items\":[{\"name\":\"white_shirt\",\"material_type\":\"cotton\",\"color_group\":\"white\",\"weight_g\":280,\"contamination_level\":\"low\"},{\"name\":\"denim_pants\",\"material_type\":\"denim\",\"color_group\":\"denim\",\"weight_g\":820,\"contamination_level\":\"medium\",\"has_zipper\":true,\"is_new_clothing\":true},{\"name\":\"knit_sweater\",\"material_type\":\"knit\",\"color_group\":\"dark\",\"weight_g\":430,\"contamination_level\":\"low\"}],\"sensor_data\":[{\"sensor_type\":\"weight\",\"measured_value\":1.65,\"unit\":\"kg\"}],\"wash_status\":{\"contamination_level\":\"medium\",\"load_status_percent\":72}}"
```

리스크 낮은 케이스:

```bash
curl.exe -X POST "http://127.0.0.1:8000/api/fabric-damage/solution" -H "Content-Type: application/json" -d "{\"washer_capacity_kg\":12,\"items\":[{\"name\":\"cotton_tshirt\",\"material_type\":\"cotton\",\"color_group\":\"light\",\"weight_g\":220,\"contamination_level\":\"low\"},{\"name\":\"poly_shirt\",\"material_type\":\"polyester\",\"color_group\":\"light\",\"weight_g\":180,\"contamination_level\":\"low\"}],\"sensor_data\":[{\"sensor_type\":\"weight\",\"measured_value\":450,\"unit\":\"g\"}]}"
```

리스크 높은 케이스:

```bash
curl.exe -X POST "http://127.0.0.1:8000/api/fabric-damage/solution" -H "Content-Type: application/json" -d "{\"washer_capacity_kg\":9,\"items\":[{\"name\":\"silk_blouse\",\"material_type\":\"silk\",\"color_group\":\"white\",\"weight_g\":140,\"contamination_level\":\"low\",\"is_new_clothing\":true},{\"name\":\"denim_jacket\",\"material_type\":\"denim\",\"color_group\":\"denim\",\"weight_g\":900,\"contamination_level\":\"medium\",\"has_zipper\":true},{\"name\":\"wool_knit\",\"material_type\":\"wool\",\"color_group\":\"dark\",\"weight_g\":420,\"contamination_level\":\"low\"},{\"name\":\"dirty_towel\",\"material_type\":\"towel\",\"color_group\":\"dark\",\"weight_g\":500,\"contamination_level\":\"high\"}],\"sensor_data\":[{\"sensor_type\":\"weight\",\"measured_value\":2.1,\"unit\":\"kg\"}],\"wash_status\":{\"load_status_percent\":88,\"contamination_level\":\"high\"}}"
```

## 문서 기준 디렉토리

- `app/laundry_timing`: 세탁 타이밍 추천 기능
- `app/fabric_damage`: 섬유 손상 가이드
- `app/laundry_progress`: 세탁 진행 상황 알림
- `app/drying_optimization`: 건조 방법 최적화 서비스
- `app/utils`: 여러 기능에서 공통으로 사용하는 유틸리티
