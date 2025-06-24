from typing import List, Optional
from ..schemas.kpi import KPIDefinition, KPIResponse
from datetime import datetime
from pathlib import Path
import json

class KPIRepository:
    def add_kpi(self, kpi: KPIDefinition, user: str) -> KPIResponse:
        raise NotImplementedError
    def list_kpis(self) -> List[KPIResponse]:
        raise NotImplementedError
    def get_kpi_by_name(self, name: str) -> Optional[KPIResponse]:
        raise NotImplementedError

class KPIJsonRepository(KPIRepository):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def _load_kpis(self) -> List[dict]:
        if not self.file_path.exists():
            return []
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _save_kpis(self, kpis: List[dict]):
        with open(self.file_path, "w") as f:
            json.dump(kpis, f, default=str, indent=2)

    def add_kpi(self, kpi: KPIDefinition, user: str) -> KPIResponse:
        kpis = self._load_kpis()
        if any(existing["name"] == kpi.name for existing in kpis):
            raise ValueError("KPI with this name already exists.")
        kpi_data = kpi.dict()
        kpi_data["created_by"] = user
        kpi_data["created_at"] = datetime.utcnow().isoformat()
        kpis.append(kpi_data)
        self._save_kpis(kpis)
        return KPIResponse(**kpi_data)

    def list_kpis(self) -> List[KPIResponse]:
        kpis = self._load_kpis()
        return [KPIResponse(**k) for k in kpis]

    def get_kpi_by_name(self, name: str) -> Optional[KPIResponse]:
        kpis = self._load_kpis()
        for k in kpis:
            if k["name"] == name:
                return KPIResponse(**k)
        return None 