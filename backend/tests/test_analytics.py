from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db import Base
from app import seed as sd, services as sv
@pytest.fixture(scope="module")
def db():
    e = create_engine("sqlite://", poolclass=StaticPool); Base.metadata.create_all(e)
    with Session(e) as s:
        sd.seed(s, n_orders=300); yield s
def test_margin_is_ratio_of_totals(db):
    t = sv._totals(db); assert t["margin_pct"] == pytest.approx(t["profit"] / t["revenue"] * 100)
def test_orders_are_distinct_not_lines(db):
    from sqlalchemy import select, func
    from app.models import Order
    lines = db.scalar(select(func.count()).select_from(Order)); assert sv._totals(db)["orders"] < lines
def test_date_bounds_inclusive_and_trend_reconciles(db):
    s, e = date(2025, 1, 1), date(2025, 12, 31)
    t = sv._totals(db, start=s, end=e)
    assert sum(m["revenue"] for m in sv.sales_trend(db, s, e)) == pytest.approx(t["revenue"])
    assert sum(r["revenue"] for r in sv.regions(db, s, e)) == pytest.approx(t["revenue"])
def test_filter_and_empty(db):
    assert sv._totals(db, region="West")["revenue"] < sv._totals(db)["revenue"]
    z = sv._totals(db, start=date(1990, 1, 1), end=date(1990, 1, 2)); assert z["margin_pct"] == 0 and z["aov"] == 0
def test_growth_unavailable_when_no_prior(db):
    assert sv.overview(db, date(2024, 1, 1), date(2024, 3, 31))["growth_pct"]["revenue"] is None
