from ..utils.data_loader import load_timeseries
from ..utils.db_writer import write_risks
from .affordability import calc_affordability
from .composite_index import calc_composite


def run_risk_pipeline(conn, city: str, target: str):
    """
    Calculate risk indices for a given city + target
    and write results into risk_predictions.
    """
    df = load_timeseries(conn, target, city)

    results = []
    results.append(calc_affordability(df, city))

    # TODO: add price_to_rent.py, inventory.py later
    composite = calc_composite(results, city)
    results.append(composite)

    write_risks(conn, results)
