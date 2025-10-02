# Risk Models

## Purpose
Assess **market fragility and stress** by computing risk indices.

## Current Components
- **Affordability index** (`affordability.py`)
- **Price-to-rent ratio** (planned)
- **Inventory stress index** (planned)
- **Composite index** (`composite_index.py`)

## Pipeline
- `risk_pipeline.py` → aggregates individual indices into `risk_predictions`.

## Example Usage

Random Forest / Logistic Regression risk classifier.