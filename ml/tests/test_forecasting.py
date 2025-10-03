#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for forecasting models (Prophet, ARIMA).
"""

import unittest
import pandas as pd

from ml.src.models.forecasting.prophet_model import run_prophet
from ml.src.models.forecasting.arima_model import run_arima


def sample_df():
    dates = pd.date_range("2020-01-01", periods=24, freq="ME")
    values = [100 + i * 5 for i in range(24)]  # simple upward trend
    return pd.DataFrame({"date": dates, "value": values})


class TestForecasting(unittest.TestCase):
    """Test suite for forecasting models"""

    def test_prophet_forecast(self):
        df = sample_df()
        results = run_prophet(df, "Kelowna", "price")
        self.assertEqual(len(results), 12)
        self.assertIn("yhat", results[0])
        self.assertIn("city", results[0])

    def test_arima_forecast(self):
        df = sample_df()
        results = run_arima(df, "Kelowna", "price")
        self.assertEqual(len(results), 12)
        self.assertIn("yhat", results[0])
        self.assertIn("target", results[0])


if __name__ == "__main__":
    unittest.main()
