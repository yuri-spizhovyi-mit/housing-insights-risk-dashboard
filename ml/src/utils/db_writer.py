# ml/src/utils/db_writer.py
import pandas as pd


def write_forecasts(conn_or_engine, results):
    """
    Write Prophet forecast results to public.model_predictions.
    Supports both psycopg2 and SQLAlchemy connections.
    """
    if results is None:
        print("[WARN] Forecast results are None — skipping write.")
        return 0

    if isinstance(results, pd.DataFrame):
        if results.empty:
            print("[WARN] Forecast DataFrame is empty — skipping write.")
            return 0
        df = results.copy()
    elif isinstance(results, list):
        if len(results) == 0:
            print("[WARN] Forecast results list is empty — skipping write.")
            return 0
        df = pd.DataFrame(results)
    else:
        print(f"[ERROR] Unsupported forecast results type: {type(results)}")
        return 0

    # Ensure required Prophet columns exist
    required = {"predict_date", "yhat", "yhat_lower", "yhat_upper"}
    if not required.issubset(df.columns):
        print(
            f"[ERROR] Forecast dataframe missing columns: {required - set(df.columns)}"
        )
        return 0

    # Add default metadata columns if missing
    meta_cols = [
        "model_name",
        "target",
        "horizon_months",
        "city",
        "property_type",
        "beds",
        "baths",
        "sqft_min",
        "sqft_max",
        "year_built_min",
        "year_built_max",
        "features_version",
        "model_artifact_uri",
    ]
    for c in meta_cols:
        if c not in df.columns:
            df[c] = None

    # Write using SQLAlchemy (preferred)
    try:
        if hasattr(conn_or_engine, "engine"):  # context-like wrapper
            engine = conn_or_engine.engine
        else:
            engine = conn_or_engine

        df.to_sql(
            "model_predictions",
            engine,
            schema="public",
            if_exists="append",
            index=False,
            method="multi",
        )
        print(f"[OK] Inserted {len(df)} forecast rows → model_predictions")

    except Exception as e:
        print(f"[ERROR] SQLAlchemy insert failed: {e}")
        # Fallback for raw psycopg2
        try:
            with conn_or_engine.cursor() as cur:
                for _, r in df.iterrows():
                    cur.execute(
                        """
                        INSERT INTO public.model_predictions (
                            model_name, target, horizon_months, city,
                            property_type, beds, baths,
                            sqft_min, sqft_max, year_built_min, year_built_max,
                            predict_date, yhat, yhat_lower, yhat_upper,
                            features_version, model_artifact_uri
                        )
                        VALUES (
                            %(model_name)s, %(target)s, %(horizon_months)s, %(city)s,
                            %(property_type)s, %(beds)s, %(baths)s,
                            %(sqft_min)s, %(sqft_max)s, %(year_built_min)s, %(year_built_max)s,
                            %(predict_date)s, %(yhat)s, %(yhat_lower)s, %(yhat_upper)s,
                            %(features_version)s, %(model_artifact_uri)s
                        );
                        """,
                        r.to_dict(),
                    )
            conn_or_engine.commit()
            print(
                f"[OK] Inserted {len(df)} forecast rows → model_predictions (psycopg2 fallback)"
            )
        except Exception as e2:
            print(f"[ERROR] Psycopg2 insert failed: {e2}")

    return len(df)


def write_risks(conn_or_engine, results):
    """Write ARIMA or computed risk indices to public.risk_predictions."""
    if results is None:
        print("[WARN] No risk results to write.")
        return 0
    if isinstance(results, pd.DataFrame):
        if results.empty:
            print("[WARN] Risk DataFrame empty.")
            return 0
        df = results.copy()
    else:
        df = pd.DataFrame(results)

    required = {"city", "risk_type", "predict_date", "risk_value"}
    if not required.issubset(df.columns):
        print(f"[ERROR] risk_predictions missing columns: {required - set(df.columns)}")
        return 0

    try:
        engine = (
            conn_or_engine.engine
            if hasattr(conn_or_engine, "engine")
            else conn_or_engine
        )
        df.to_sql(
            "risk_predictions",
            engine,
            schema="public",
            if_exists="append",
            index=False,
            method="multi",
        )
        print(f"[OK] Inserted {len(df)} rows → risk_predictions")
        return len(df)
    except Exception as e:
        print(f"[ERROR] write_risks() failed: {e}")
        return 0


def write_anomalies(conn_or_engine, results):
    """Write IsolationForest anomalies to public.anomaly_signals."""
    if results is None:
        print("[WARN] No anomaly results to write.")
        return 0
    if isinstance(results, pd.DataFrame):
        if results.empty:
            print("[WARN] Anomaly DataFrame empty.")
            return 0
        df = results.copy()
    else:
        df = pd.DataFrame(results)

    required = {"city", "target", "detect_date", "anomaly_score", "is_anomaly"}
    if not required.issubset(df.columns):
        print(f"[ERROR] anomaly_signals missing columns: {required - set(df.columns)}")
        return 0

    try:
        engine = (
            conn_or_engine.engine
            if hasattr(conn_or_engine, "engine")
            else conn_or_engine
        )
        df.to_sql(
            "anomaly_signals",
            engine,
            schema="public",
            if_exists="append",
            index=False,
            method="multi",
        )
        print(f"[OK] Inserted {len(df)} rows → anomaly_signals")
        return len(df)
    except Exception as e:
        print(f"[ERROR] write_anomalies() failed: {e}")
        return 0
