from prism.kpi_engine.schemas.kpi import KPIDefinition, KPIResponse
from prism.kpi_engine.repositories.kpi_repository import KPIJsonRepository
from prism.kpi_engine.utils.schema_mock import load_mock_schema
from prism.kpi_engine.utils.validate_formula import validate_formula, FormulaValidationError
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException

# Instantiate the repository (swap this with a DB repo later)
repo = KPIJsonRepository(Path(__file__).parent.parent / "kpi_registry.json")

def register_kpi(kpi: KPIDefinition, user: str) -> KPIResponse:
    schema = load_mock_schema()
    try:
        validate_formula(kpi.formula, schema)
        return repo.add_kpi(kpi, user)
    except FormulaValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def list_kpis() -> List[KPIResponse]:
    return repo.list_kpis()

def get_kpi_by_name(name: str) -> Optional[KPIResponse]:
    return repo.get_kpi_by_name(name) 