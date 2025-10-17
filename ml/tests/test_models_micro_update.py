#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for micro-forecast scaling module.
"""

import unittest
import pandas as pd
from ml.src.models.run_models_micro_update import scale_micro_forecasts


def sample_macro_forecasts():
    """Synthetic macro forecast dataset"""
    dates = pd.date_range("2025-01-01", periods=12, freq="M")
    return pd.DataFrame({
        "city": ["Kelowna"] * 12,
        "date": dates,
        "value": [1500 + i * 10 for i in range(12)],
    })


def sample_ratios():
    """Synthetic rent ratio table"""
    return pd.DataFrame({
        "city": ["Kelowna", "Kelowna"],
        "property_type": ["Condo", "House"],
        "beds": [1, 2],
        "rent_ratio": [0.9, 1.2],
    })


class TestMicroScaling(unittest.TestCase):
    """Test suite for micro-forecast scaling"""

    def test_scaled_forecasts(self):
        macro = sample_macro_forecasts()
        ratios = sample_ratios()
        results = scale_micro_forecasts(macro, ratios)

        # Expected number of results = len(macro) * len(ratios)
        self.assertEqual(len(results), len(macro) * len(ratios))
        # Ensure scaling applied properly
        first_scaled = results.iloc[0]["value"]
        base_value = macro.iloc[0]["value"]
        self.assertNotEqual(first_scaled, base_value)


if __name__ == "__main__":
    unittest.main()
