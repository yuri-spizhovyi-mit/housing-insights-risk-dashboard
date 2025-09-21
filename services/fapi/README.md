# FastAPI Service

Python service exposing forecasts from Neon DB.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```text
services/
  └── fastapi/
        ├── main.py              # FastAPI entrypoint
        ├── db.py                # DB connection helper
        ├── routes/
        │     ├── forecast.py    # /forecast/{city}
        │     ├── risk.py        # /risk/{city}
        │     ├── sentiment.py   # /sentiment/{city}
        │     ├── anomalies.py   # /anomalies/{city}
        │     ├── report.py      # /report/{city}.pdf
        │     └── cities.py      # /cities
        ├── requirements.txt
        ├── vercel.json
        └── README.md
```
