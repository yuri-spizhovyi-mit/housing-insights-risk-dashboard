import datetime as dt
from ml.src.etl import rentals_ca, base


def _make_ctx():
    ctx = base.Context(run_date=dt.date(2025, 8, 15))
    ctx.params = {}
    return ctx


def test_auto_discovery_happy_path(tmp_path, monkeypatch):
    """
    Simulate crawling success:
    - discover_latest_tabular_asset returns a CSV URL
    - load_via_http reads our local temp CSV and returns bytes
    - ensure normalization + upsert are executed
    """
    # Create a tiny CSV that looks like Rentals.ca output
    csv_path = tmp_path / "auto_found.csv"
    csv_path.write_text(
        "city,bedroom,median_rent,month\n"
        "Vancouver,1 Bedroom,3125,2025-08\n"
        "Toronto,2 Bedroom,3620,2025-08\n"
        "Kelowna,Studio,1820,2025-08\n",
        encoding="utf-8",
    )

    # Pretend our crawler found this URL (it won't actually be fetched)
    discovered_url = "https://example.com/rentals_auto.csv"
    monkeypatch.setattr(
        rentals_ca,
        "discover_latest_tabular_asset",
        lambda session: discovered_url,
        raising=True,
    )

    # Instead of real HTTP, return the bytes from our temp CSV
    def fake_load_via_http(session, url):
        assert url == discovered_url
        raw = csv_path.read_bytes()
        return raw, "rentals_auto.csv", "text/csv"

    monkeypatch.setattr(rentals_ca, "load_via_http", fake_load_via_http, raising=True)

    # Capture what would be written to DB
    captured = {}

    def fake_upsert(df, ctx):
        captured["df"] = df.copy()

    monkeypatch.setattr(base, "write_rents_upsert", fake_upsert, raising=True)

    # Provide a session if your base lacks get_session
    import requests

    monkeypatch.setattr(
        rentals_ca.base, "get_session", lambda ctx: requests.Session(), raising=False
    )

    # Run with auto mode (no explicit path/url/endpoint)
    ctx = _make_ctx()
    ctx.params["rentals_ca_auto"] = True

    tidy = rentals_ca.run(ctx)

    out = captured["df"]
    assert not out.empty
    # Correct columns and normalization
    assert set(out.columns) == {"city", "date", "bedroom_type", "median_rent", "source"}
    assert set(out["city"]) == {"Vancouver", "Toronto", "Kelowna"}
    assert set(out["bedroom_type"]) == {"0BR", "1BR", "2BR"}
    assert set(out["date"].astype(str)) == {"2025-08-01"}
    assert (out["source"] == "Rentals.ca").all()
