# Anomaly Detection

## Purpose
Detect **unusual market movements** (e.g., sudden spikes in rent or prices).

## Current Methods
- **Isolation Forest** (`isolation_forest.py`)
- Prophet changepoints (planned)
- Statistical z-score detector (planned)

## Pipeline
- `anomaly_pipeline.py` → inserts anomaly signals into `anomaly_signals`.

## Example Usage

Isolation Forest anomaly detection.
