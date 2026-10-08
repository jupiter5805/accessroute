from fastapi import FastAPI

app = FastAPI(
    title="AccessRoute",
    description="Accessibility-aware routing API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AccessRoute",
    }
