from fastapi import FastAPI
from api import session_management, ai_role_management
import uvicorn

app = FastAPI()

# Example router (you can add your own routers here)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(session_management.router, prefix="/api")
app.include_router(ai_role_management.router, prefix="/api")
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=7001, reload=True)
