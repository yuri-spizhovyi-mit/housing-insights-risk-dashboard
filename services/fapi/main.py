from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fapi.routes import (
    forecast,
    risk,
    sentiment,
    report,
    cities,
    anomalies,
    model_comparison,
)

app = FastAPI(title="Housing Insights API")

# ✅ Configure CORS
origins = [
    "http://localhost:5173",  # local frontend dev
    "https://hird.netlify.app",  # deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(cities.router)
app.include_router(forecast.router)
app.include_router(risk.router)
app.include_router(sentiment.router)
app.include_router(anomalies.router)
app.include_router(report.router)
app.include_router(model_comparison.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "fastapi"}
