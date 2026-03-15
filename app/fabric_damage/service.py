from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.fabric_damage.schemas import (
    ClothingItemInput,
    ContaminationLevel,
    DetectedItemResponse,
    FabricDamageSolutionRequest,
    FabricDamageSolutionResponse,
    RiskAssessmentResponse,
    RiskItemResponse,
    SensorAnalysisResponse,
    WashRecommendationResponse,
)


@dataclass(frozen=True)
class MaterialProfile:
    delicate: bool
    rough: bool
    absorbent: bool
    max_temp: int
    preferred_spin: str
    detergent_type: str
    care_labels: tuple[str, ...]


MATERIAL_PROFILES: dict[str, MaterialProfile] = {
    "cotton": MaterialProfile(False, False, True, 40, "medium", "중성세제", ("표준 세탁 가능",)),
    "linen": MaterialProfile(True, False, True, 30, "low", "중성세제", ("저온 세탁 권장", "강한 탈수 주의")),
    "wool": MaterialProfile(True, False, False, 30, "low", "울 전용 세제", ("울 코스 권장", "마찰 주의")),
    "silk": MaterialProfile(True, False, False, 30, "low", "실크 전용 세제", ("단독 세탁 권장", "건조기 금지")),
    "knit": MaterialProfile(True, True, False, 30, "low", "중성세제", ("세탁망 권장", "보풀 주의")),
    "denim": MaterialProfile(False, True, False, 30, "medium", "중성세제", ("이염 주의",)),
    "polyester": MaterialProfile(False, False, False, 40, "medium", "중성세제", ("표준 세탁 가능",)),
    "nylon": MaterialProfile(False, False, False, 30, "low", "중성세제", ("저온 세탁 권장",)),
    "spandex": MaterialProfile(True, False, False, 30, "low", "중성세제", ("고온 세탁 금지",)),
    "towel": MaterialProfile(False, True, True, 40, "medium", "중성세제", ("보풀 발생 가능",)),
    "down": MaterialProfile(True, False, False, 30, "low", "다운 전용 세제", ("다운 코스 권장", "약한 탈수")),
    "functional": MaterialProfile(True, False, False, 30, "low", "기능성 의류 세제", ("섬유유연제 지양",)),
}

CONTAMINATION_ORDER: dict[ContaminationLevel, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


class FabricDamageSolutionService:
    def build_solution(
        self, request: FabricDamageSolutionRequest
    ) -> FabricDamageSolutionResponse:
        analyzed_items = [self._to_detected_item(item) for item in request.items]
        sensor_analysis = self._analyze_sensor_data(request)
        risk_items = self._calculate_risks(request.items, sensor_analysis.estimated_load_percent)
        risk_assessment = self._build_risk_assessment(risk_items)
        recommendation = self._build_recommendation(
            request.items,
            sensor_analysis=sensor_analysis,
            risk_assessment=risk_assessment,
        )

        return FabricDamageSolutionResponse(
            wash_id=request.wash_id,
            member_id=request.member_id,
            washer_id=request.washer_id,
            analyzed_items=analyzed_items,
            sensor_analysis=sensor_analysis,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
        )

    def _to_detected_item(self, item: ClothingItemInput) -> DetectedItemResponse:
        profile = MATERIAL_PROFILES[item.material_type]
        care_labels = list(profile.care_labels)
        if item.is_new_clothing:
            care_labels.append("새 옷은 첫 세탁 시 이염 주의")
        if item.has_zipper:
            care_labels.append("지퍼는 잠그고 뒤집어서 세탁 권장")
        if item.has_print:
            care_labels.append("프린팅 손상 방지를 위해 뒤집기 권장")

        return DetectedItemResponse(
            name=item.name,
            material_type=item.material_type,
            color_group=item.color_group,
            weight_g=item.weight_g,
            contamination_level=item.contamination_level,
            care_labels=care_labels,
        )

    def _analyze_sensor_data(
        self, request: FabricDamageSolutionRequest
    ) -> SensorAnalysisResponse:
        total_weight_g = round(sum(item.weight_g for item in request.items), 1)
        sensor_weight_g = self._extract_sensor_weight_g(request.sensor_data)
        effective_weight_g = sensor_weight_g or total_weight_g

        # 세탁기 용량 대비 현재 투입량을 백분율로 환산한다.
        estimated_load_percent = min(
            100, round((effective_weight_g / (request.washer_capacity_kg * 1000)) * 100)
        )
        dominant_contamination_level = self._dominant_contamination_level(request.items)
        notes: list[str] = []

        if sensor_weight_g is not None and abs(sensor_weight_g - total_weight_g) > 300:
            notes.append("센서 무게와 입력 무게 차이가 커서 적재량 재확인을 권장합니다.")

        if request.wash_status and request.wash_status.load_status_percent is not None:
            notes.append(
                f"세탁기 상태 적재율 입력값 {request.wash_status.load_status_percent}%를 함께 참고하세요."
            )

        if estimated_load_percent >= 85:
            notes.append("적재율이 높아 섬유 마찰과 구김 위험이 증가합니다.")

        if not notes:
            notes.append("입력된 세탁물과 센서 기준으로 안정적인 분석이 가능합니다.")

        return SensorAnalysisResponse(
            total_weight_g=total_weight_g,
            sensor_weight_g=sensor_weight_g,
            estimated_load_percent=estimated_load_percent,
            dominant_contamination_level=dominant_contamination_level,
            notes=notes,
        )

    def _calculate_risks(
        self, items: list[ClothingItemInput], load_percent: int
    ) -> list[RiskItemResponse]:
        risk_items = [
            self._build_color_bleeding_risk(items),
            self._build_pilling_risk(items),
            self._build_deformation_risk(items, load_percent),
            self._build_contamination_transfer_risk(items),
        ]
        return sorted(risk_items, key=lambda item: item.score, reverse=True)

    def _build_color_bleeding_risk(self, items: list[ClothingItemInput]) -> RiskItemResponse:
        light_items = [item.name for item in items if item.color_group in {"white", "light"}]
        bleed_items = [
            item.name
            for item in items
            if item.color_group in {"dark", "vivid", "black", "denim"} or item.is_new_clothing
        ]
        score = 15
        reasons: list[str] = []

        if light_items and bleed_items:
            score = 78 if any(item.is_new_clothing for item in items) else 64
            reasons.append("밝은 색상 의류와 이염 가능 의류가 함께 섞여 있습니다.")
        if any(item.color_group == "denim" for item in items):
            score += 10
            reasons.append("데님 소재는 첫 세탁과 진한 색상에서 이염 위험이 큽니다.")
        if any(item.color_group == "vivid" for item in items):
            score += 6
            reasons.append("원색 계열 의류는 염료 빠짐 가능성을 함께 고려해야 합니다.")

        score = min(score, 95)
        if not reasons:
            reasons.append("색상 조합상 큰 이염 징후는 낮습니다.")

        return RiskItemResponse(
            category="이염 위험",
            score=score,
            reasons=reasons,
            caution_items=bleed_items[:3] + light_items[:3],
        )

    def _build_pilling_risk(self, items: list[ClothingItemInput]) -> RiskItemResponse:
        delicate_items = [
            item.name for item in items if MATERIAL_PROFILES[item.material_type].delicate
        ]
        rough_items = [item.name for item in items if MATERIAL_PROFILES[item.material_type].rough]
        zipper_items = [item.name for item in items if item.has_zipper]
        score = 18
        reasons: list[str] = []

        if delicate_items and rough_items:
            score = 68
            reasons.append("니트·울 등 민감 소재와 마찰이 큰 소재가 함께 들어 있습니다.")
        if zipper_items and delicate_items:
            score += 12
            reasons.append("지퍼/금속 부자재가 민감 소재를 긁을 수 있습니다.")
        if any(item.material_type == "knit" for item in items):
            score += 8
            reasons.append("니트류는 보풀과 늘어남에 특히 취약합니다.")

        score = min(score, 92)
        if not reasons:
            reasons.append("보풀 유발 조합은 상대적으로 낮은 편입니다.")

        return RiskItemResponse(
            category="보풀/마찰 위험",
            score=score,
            reasons=reasons,
            caution_items=(delicate_items + rough_items + zipper_items)[:4],
        )

    def _build_deformation_risk(
        self, items: list[ClothingItemInput], load_percent: int
    ) -> RiskItemResponse:
        delicate_items = [
            item.name for item in items if MATERIAL_PROFILES[item.material_type].delicate
        ]
        heavy_items = [item.name for item in items if item.weight_g >= 700]
        score = 20 + max(load_percent - 60, 0) // 2
        reasons: list[str] = []

        if delicate_items and heavy_items:
            score = max(score, 72)
            reasons.append("민감 소재와 무거운 세탁물이 함께 있어 형태 변형 가능성이 큽니다.")
        if load_percent >= 85:
            score += 10
            reasons.append("과적 상태에 가까워 세탁 중 압착과 구김이 심해질 수 있습니다.")
        if any(item.material_type in {"wool", "silk", "down"} for item in items):
            score += 8
            reasons.append("울, 실크, 다운 소재는 강한 회전에 취약합니다.")

        score = min(score, 95)
        if not reasons:
            reasons.append("형태 변형 위험은 중간 이하 수준입니다.")

        return RiskItemResponse(
            category="수축/변형 위험",
            score=score,
            reasons=reasons,
            caution_items=(delicate_items + heavy_items)[:4],
        )

    def _build_contamination_transfer_risk(self, items: list[ClothingItemInput]) -> RiskItemResponse:
        low_items = [item.name for item in items if item.contamination_level == "low"]
        high_items = [item.name for item in items if item.contamination_level == "high"]
        score = 16
        reasons: list[str] = []

        if low_items and high_items:
            score = 74
            reasons.append("오염도가 높은 세탁물과 낮은 세탁물이 함께 들어 있습니다.")
        if len(high_items) >= 2:
            score += 8
            reasons.append("강한 오염 의류가 다수라 표준 세탁만으로는 재오염 가능성이 있습니다.")

        score = min(score, 90)
        if not reasons:
            reasons.append("오염도 편차가 커 보이지 않습니다.")

        return RiskItemResponse(
            category="오염 전이 위험",
            score=score,
            reasons=reasons,
            caution_items=(high_items + low_items)[:4],
        )

    def _build_risk_assessment(
        self, risk_items: list[RiskItemResponse]
    ) -> RiskAssessmentResponse:
        top_risks = risk_items[:3]
        overall_score = round(sum(item.score for item in top_risks) / len(top_risks))
        separate_wash_required = any(item.score >= 70 for item in top_risks)

        if overall_score >= 75:
            summary = "혼합 세탁 위험이 높아 분리 세탁 중심의 세탁 계획이 필요합니다."
        elif overall_score >= 50:
            summary = "세탁은 가능하지만 일부 민감 의류는 보호 조치가 필요합니다."
        else:
            summary = "현재 조합은 비교적 안정적이지만 기본 보호 설정은 유지하는 편이 좋습니다."

        return RiskAssessmentResponse(
            overall_score=overall_score,
            summary=summary,
            top_risks=top_risks,
            separate_wash_required=separate_wash_required,
        )

    def _build_recommendation(
        self,
        items: list[ClothingItemInput],
        *,
        sensor_analysis: SensorAnalysisResponse,
        risk_assessment: RiskAssessmentResponse,
    ) -> WashRecommendationResponse:
        profiles = [MATERIAL_PROFILES[item.material_type] for item in items]
        water_temperature_celsius = min(profile.max_temp for profile in profiles)
        delicate_exists = any(profile.delicate for profile in profiles)
        high_contamination_exists = any(item.contamination_level == "high" for item in items)

        if risk_assessment.separate_wash_required or delicate_exists:
            course = "섬세 코스"
        elif high_contamination_exists:
            course = "표준 코스 + 오염 집중 옵션"
        else:
            course = "표준 코스"

        if delicate_exists or sensor_analysis.estimated_load_percent >= 85:
            spin_level = "low"
        elif sensor_analysis.estimated_load_percent >= 70:
            spin_level = "medium"
        else:
            spin_level = "high"

        detergent_candidates = Counter(profile.detergent_type for profile in profiles)
        detergent_type = detergent_candidates.most_common(1)[0][0]

        immediate_actions = self._build_immediate_actions(
            items,
            risk_assessment=risk_assessment,
            sensor_analysis=sensor_analysis,
        )
        separating_groups = self._build_separating_groups(items)

        if any(item.material_type in {"down", "wool", "silk"} for item in items):
            drying_tip = "열 건조보다 자연 건조 또는 저온 건조를 권장합니다."
        elif any(item.material_type == "functional" for item in items):
            drying_tip = "기능성 의류는 건조기 고온 설정을 피해주세요."
        else:
            drying_tip = "표준 탈수 후 통풍이 잘 되는 환경에서 건조하면 좋습니다."

        return WashRecommendationResponse(
            course=course,
            water_temperature_celsius=water_temperature_celsius,
            spin_level=spin_level,
            detergent_type=detergent_type,
            drying_tip=drying_tip,
            immediate_actions=immediate_actions,
            separating_groups=separating_groups,
        )

    def _build_immediate_actions(
        self,
        items: list[ClothingItemInput],
        *,
        risk_assessment: RiskAssessmentResponse,
        sensor_analysis: SensorAnalysisResponse,
    ) -> list[str]:
        actions: list[str] = []

        if risk_assessment.separate_wash_required:
            actions.append("이염 또는 손상 위험이 큰 의류는 분리 세탁하세요.")

        if any(item.has_zipper for item in items):
            actions.append("지퍼와 단추는 잠그고, 민감 의류는 세탁망에 넣어주세요.")

        if any(item.has_print for item in items):
            actions.append("프린팅 의류는 뒤집어서 세탁하면 마찰 손상을 줄일 수 있습니다.")

        if sensor_analysis.estimated_load_percent >= 85:
            actions.append("한 번에 모두 세탁하지 말고 2회로 나누면 변형 위험을 줄일 수 있습니다.")

        if any(item.is_new_clothing for item in items):
            actions.append("새 옷은 첫 세탁 시 단독 세탁을 우선 검토하세요.")

        if not actions:
            actions.append("현재 조합은 표준 세탁이 가능하지만 저온 세탁을 유지하는 편이 안전합니다.")

        return actions

    def _build_separating_groups(self, items: list[ClothingItemInput]) -> list[list[str]]:
        # 색상과 민감 소재를 우선 기준으로 세탁 묶음을 제안한다.
        delicate_group = [
            item.name
            for item in items
            if MATERIAL_PROFILES[item.material_type].delicate or item.has_print
        ]
        dark_group = [
            item.name
            for item in items
            if item.color_group in {"dark", "black", "vivid", "denim"} and item.name not in delicate_group
        ]
        normal_group = [
            item.name for item in items if item.name not in delicate_group and item.name not in dark_group
        ]

        return [group for group in (delicate_group, dark_group, normal_group) if group]

    def _extract_sensor_weight_g(self, sensor_data: list) -> float | None:
        weights: list[float] = []
        for sensor in sensor_data:
            if sensor.sensor_type != "weight":
                continue

            unit = sensor.unit.lower()
            value = float(sensor.measured_value)
            if unit == "kg":
                weights.append(value * 1000)
            elif unit == "g":
                weights.append(value)

        if not weights:
            return None
        return round(max(weights), 1)

    def _dominant_contamination_level(
        self, items: list[ClothingItemInput]
    ) -> ContaminationLevel:
        counted = Counter(item.contamination_level for item in items)
        return max(
            counted,
            key=lambda level: (counted[level], CONTAMINATION_ORDER[level]),
        )
