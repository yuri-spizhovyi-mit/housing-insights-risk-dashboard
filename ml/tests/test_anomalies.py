#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for anomaly detection models.
"""

import unittest
import pandas as pd

from ml.src.models.anomalies.isolation_forest import detect_iforest


def sample_df():
    dates = pd.date_range("2020-01-01", periods=24, freq="ME")
    values = [100] * 20 + [500, 600, 700, 800]  # spike anomalies
    return pd.DataFrame({"date": dates, "value": values})


class TestAnomalies(unittest.TestCase):
    """Test suite for anomaly detection"""

    def test_isolation_forest(self):
        df = sample_df()
        results = detect_iforest(df, "Vancouver", "rent")
        self.assertEqual(len(results), len(df))
        # Ensure at least one anomaly is detected
        anomalies = [r for r in results if r["is_anomaly"]]
        self.assertTrue(len(anomalies) > 0)


if __name__ == "__main__":
    unittest.main()
