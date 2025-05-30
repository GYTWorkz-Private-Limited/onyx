from fastapi import FastAPI
from api import kpi  # <-- absolute import, since api is a sibling of server.py

app = FastAPI()
app.include_router(kpi.router, prefix="/kpi")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


