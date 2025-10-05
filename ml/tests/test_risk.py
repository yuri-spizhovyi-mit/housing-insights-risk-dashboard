#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for risk models (affordability, composite).
"""

import unittest
import pandas as pd

from ml.src.models.risk.affordability import calc_affordability
from ml.src.models.risk.composite_index import calc_composite


def sample_df():
    dates = pd.date_range("2020-01-01", periods=12, freq="ME")
    values = [500000 + i * 10000 for i in range(12)]
    return pd.DataFrame({"date": dates, "value": values})


class TestRisk(unittest.TestCase):
    """Test suite for risk models"""

    def test_affordability(self):
        df = sample_df()
        result = calc_affordability(df, "Toronto")
        self.assertEqual(result["risk_type"], "affordability")
        self.assertGreaterEqual(result["risk_value"], 0.0)
        self.assertLessEqual(result["risk_value"], 1.0)

    def test_composite_index(self):
        df = sample_df()
        comp = calc_affordability(df, "Toronto")
        result = calc_composite([comp], "Toronto")
        self.assertEqual(result["risk_type"], "composite_index")
        self.assertGreaterEqual(result["risk_value"], 0.0)
        self.assertLessEqual(result["risk_value"], 1.0)


if __name__ == "__main__":
    unittest.main()
