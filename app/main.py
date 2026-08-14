from fastapi import FastAPI

from app.routers.tasks import router as tasks_router

app = FastAPI(title="AI Automation OS", version="0.1.0")
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
