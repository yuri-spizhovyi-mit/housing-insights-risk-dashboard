#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for forecasting models: Prophet and ARIMA.
"""

import unittest
import pandas as pd
from ml.src.models.forecasting.prophet_model import run_prophet
from ml.src.models.forecasting.arima_model import run_arima


def sample_series():
    """Generate synthetic monthly time series."""
    dates = pd.date_range("2022-01-01", periods=24, freq="ME")
    values = [1200 + i * 15 for i in range(24)]  # mild upward trend
    return pd.DataFrame({"date": dates, "value": values})


class TestForecastModels(unittest.TestCase):
    """Tests for Prophet and ARIMA forecast outputs."""

    def test_prophet_returns_list_of_dicts(self):
        df = sample_series()
        forecasts = run_prophet(df, city="Kelowna", target="rent_index")

        # Verify type
        self.assertIsInstance(forecasts, list)
        self.assertGreater(len(forecasts), 0)
        self.assertIsInstance(forecasts[0], dict)

        # Check key structure
        expected_keys = {
            "model_name",
            "target",
            "horizon_months",
            "city",
            "predict_date",
            "yhat",
            "yhat_lower",
            "yhat_upper",
            "features_version",
            "model_artifact_uri",
        }
        self.assertTrue(expected_keys.issubset(forecasts[0].keys()))

        # Logical checks
        self.assertEqual(forecasts[0]["model_name"], "prophet")
        self.assertEqual(forecasts[0]["city"], "Kelowna")
        self.assertEqual(len(forecasts), 12)  # 12-month horizon
        self.assertIsInstance(forecasts[0]["yhat"], float)

    def test_arima_returns_list_of_dicts(self):
        df = sample_series()
        forecasts = run_arima(df, city="Kelowna", target="rent_index")

        # Verify type and structure
        self.assertIsInstance(forecasts, list)
        self.assertEqual(len(forecasts), 12)
        self.assertIsInstance(forecasts[0], dict)

        # Expected keys
        expected_keys = {
            "model_name",
            "target",
            "horizon_months",
            "city",
            "predict_date",
            "yhat",
            "yhat_lower",
            "yhat_upper",
            "features_version",
            "model_artifact_uri",
        }
        self.assertTrue(expected_keys.issubset(forecasts[0].keys()))

        # Logical checks
        self.assertEqual(forecasts[0]["model_name"], "arima")
        self.assertEqual(forecasts[0]["city"], "Kelowna")
        self.assertIsInstance(forecasts[0]["yhat"], float)


if __name__ == "__main__":
    unittest.main()
