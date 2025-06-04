# KPI Engine

A simple service to register and manage custom KPIs using formula-based definitions.

## Quickstart

1. Install dependencies with Poetry:
   ```bash
   poetry install
   ```
2. Run the server (using Poetry):
   ```bash
   cd prism/kpi_engine
   PYTHONPATH=../.. poetry run uvicorn server:app --reload
   ```
3. Use the API endpoints to register and list KPIs.



