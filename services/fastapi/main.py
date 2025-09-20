from fastapi import FastAPI
from routes import forecast, risk, sentiment, report, cities

app = FastAPI(title="Housing Insights API")

# Register routers
app.include_router(cities.router)
app.include_router(forecast.router)
app.include_router(risk.router)
app.include_router(sentiment.router)
# app.include_router(anomalies.router)
app.include_router(report.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "fastapi"}
