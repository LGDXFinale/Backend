from __future__ import annotations

from fastapi import APIRouter

from app.fabric_damage.schemas import (
    FabricDamageSolutionRequest,
    FabricDamageSolutionResponse,
)
from app.fabric_damage.service import FabricDamageSolutionService


router = APIRouter(prefix="/api/fabric-damage", tags=["fabric-damage"])
service = FabricDamageSolutionService()


@router.post("/solution", response_model=FabricDamageSolutionResponse)
async def create_fabric_damage_solution(
    request: FabricDamageSolutionRequest,
) -> FabricDamageSolutionResponse:
    return service.build_solution(request)
