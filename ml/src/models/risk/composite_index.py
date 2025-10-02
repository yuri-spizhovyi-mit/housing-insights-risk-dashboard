from typing import List, Dict


def calc_composite(risk_components: List[Dict], city: str):
    """
    Combine risk components into a composite index.
    Expects a list of dicts with 'risk_type' and 'risk_value'.
    """
    vals = [
        r["risk_value"] for r in risk_components if r["risk_type"] != "composite_index"
    ]

    composite = sum(vals) / len(vals) if vals else 0.0

    return {
        "city": city,
        "risk_type": "composite_index",
        "predict_date": risk_components[0]["predict_date"] if risk_components else None,
        "risk_value": composite,
        "model_name": "calc",
    }
