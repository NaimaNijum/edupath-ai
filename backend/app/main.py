from fastapi import FastAPI

from app.api.routes.health import router as health_router


app = FastAPI(
    title="EduPath AI API",
    description="Multi-Agent AI Student Opportunity Assistant",
    version="0.1.0",
)

app.include_router(health_router)