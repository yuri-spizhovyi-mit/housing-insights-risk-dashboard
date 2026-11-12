import os
import subprocess
import sys
from pathlib import Path
import pytest
from services.fapi.database_url import normalize_database_url

@pytest.mark.parametrize("scheme",["postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"])
def test_postgres_uses_installed_driver(scheme):
    url=normalize_database_url(f"{scheme}://user:p%40ss@db.example/test?sslmode=require")
    assert url.drivername=="postgresql+psycopg2"
    assert url.password=="p@ss"
    assert url.query["sslmode"]=="require"

def test_sqlite_unchanged():
    assert normalize_database_url("sqlite://").drivername=="sqlite"

def test_vercel_entrypoint_starts_with_postgres_url():
    root=Path(__file__).resolve().parents[3]
    env={**os.environ,"DATABASE_URL":"postgresql://test:test@localhost/test", "PYTHONPATH":str(root/"services"), "MPLCONFIGDIR":str(root/".cache"/"matplotlib")}
    result=subprocess.run([sys.executable,"-c","from fapi.main import app; assert app is not None"],cwd=root,env=env,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
