#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for core forecasting pipeline (Prophet/ARIMA)
"""

import unittest
import pandas as pd

from ml.src.models.forecast_prophet import forecast_prophet
from ml.src.models.forecast_arima import forecast_arima


def sample_series():
    """Generate simple monthly data with trend"""
    dates = pd.date_range("2020-01-01", periods=24, freq="M")
    values = [100 + i * 2 for i in range(24)]  # upward trend
    return pd.DataFrame({"date": dates, "value": values})


class TestForecastModels(unittest.TestCase):
    """Test suite for Prophet and ARIMA forecasts"""

    def test_prophet_forecast_length(self):
        df = sample_series()
        result = forecast_prophet(df, horizon=12)
        # Check we got 12 forecast points
        self.assertEqual(len(result), 12)
        # Ensure expected keys exist
        self.assertTrue(all(k in result.columns for k in ["date", "value", "lower", "upper"]))

    def test_arima_forecast_length(self):
        df = sample_series()
        result = forecast_arima(df, horizon=12)
        self.assertEqual(len(result), 12)
        self.assertTrue("value" in result.columns)


if __name__ == "__main__":
    unittest.main()
