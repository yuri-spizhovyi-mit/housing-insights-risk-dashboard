# Features

This folder contains **feature engineering code** for housing market modeling.

## Purpose
- Transform raw ETL data into **model-ready features**.
- Provide reusable functions for **time series forecasting** and **machine learning**.

## Examples
- Lag features: `rent_t-1`, `price_t-12`.
- Growth rates: month-over-month, year-over-year % changes.
- Rolling statistics: moving averages, volatility measures.
- External signals: macroeconomic data, permits, demographics.

## Usage
Feature modules here will be imported into forecasting pipelines (e.g., LightGBM) or risk models.

