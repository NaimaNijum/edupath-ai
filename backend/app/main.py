from fastapi import FastAPI

app = FastAPI(
    title="EduPath AI API",
    description="Multi-Agent AI Student Opportunity Assistant",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "edupath-api",
    }
