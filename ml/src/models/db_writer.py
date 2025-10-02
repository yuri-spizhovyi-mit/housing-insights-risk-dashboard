import psycopg2

def write_forecasts(conn, results):
    with conn.cursor() as cur:
        for r in results:
            cur.execute("""
                INSERT INTO model_predictions
                (model_name, target, horizon_months, city,
                 predict_date, yhat, yhat_lower, yhat_upper,
                 features_version, model_artifact_uri)
                VALUES (%(model_name)s, %(target)s, %(horizon_months)s, %(city)s,
                        %(predict_date)s, %(yhat)s, %(yhat_lower)s, %(yhat_upper)s,
                        %(features_version)s, %(model_artifact_uri)s)
            """, r)
    conn.commit()


def write_risks(conn, results):
    with conn.cursor() as cur:
        for r in results:
            cur.execute("""
                INSERT INTO risk_predictions
                (city, risk_type, predict_date, risk_value, model_name)
                VALUES (%(city)s, %(risk_type)s, %(predict_date)s, %(risk_value)s, %(model_name)s)
            """, r)
    conn.commit()


def write_anomalies(conn, results):
    with conn.cursor() as cur:
        for r in results:
            cur.execute("""
                INSERT INTO anomaly_signals
                (city, target, detect_date, anomaly_score, is_anomaly, model_name)
                VALUES (%(city)s, %(target)s, %(detect_date)s, %(anomaly_score)s, %(is_anomaly)s, %(model_name)s)
            """, r)
    conn.commit()
