import os
os.environ.setdefault("DATABASE_URL","sqlite://")
from datetime import date
from types import SimpleNamespace
from services.fapi.routes.risk import get_risk
from services.fapi.routes.forecast import get_forecast
class Query:
    def __init__(self,rows):self.rows=rows
    def filter(self,*a):return self
    def order_by(self,*a):return self
    def all(self):return self.rows
class DB:
    def __init__(self,rows):self.rows=rows
    def query(self,*a):return Query(self.rows)
def test_latest_risk_and_missing_values():
    rows=[SimpleNamespace(predict_date=date(2026,2,1),risk_type="affordability",risk_value=.9),SimpleNamespace(predict_date=date(2026,1,1),risk_type="affordability",risk_value=.1)]
    result=get_risk("Calgary",DB(rows))
    assert result["breakdown"][0]["status"]=="Tight"
    assert result["breakdown"][1]["status"]=="Unavailable"
    assert result["score"] is None

def test_forecast_retains_zero_bounds_and_all_months():
    rows=[SimpleNamespace(predict_date=date(2026+i//12,i%12+1,1),yhat=0,yhat_lower=0,yhat_upper=0) for i in range(24)]
    result=get_forecast(city="Calgary",target="price",horizon="2y",model="arima",db=DB(rows))
    assert len(result["data"])==24
    assert result["data"][-1]["date"]=="2027-12-01"
    assert result["data"][0]["lower"]==0
