from fastapi import APIRouter, HTTPException, Depends
from prism.kpi_engine.controllers.kpi_controller import register_kpi, list_kpis, get_kpi_by_name
from prism.kpi_engine.schemas.kpi import KPIDefinition, KPIResponse
from prism.kpi_engine.services.auth_service import dummy_auth

router = APIRouter()

@router.post("/kpis/", response_model=KPIResponse)
def create_kpi(kpi: KPIDefinition, user=Depends(dummy_auth)):
    return register_kpi(kpi, user)

@router.get("/kpis/", response_model=list[KPIResponse])
def get_kpis(user=Depends(dummy_auth)):
    return list_kpis()

@router.get("/kpis/{name}", response_model=KPIResponse)
def get_kpi(name: str, user=Depends(dummy_auth)):
    kpi = get_kpi_by_name(name)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    return kpi 