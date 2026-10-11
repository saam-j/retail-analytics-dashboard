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
    t = sv._totals(db); assert t["gross_margin_pct"] == pytest.approx(t["gross_profit"] / t["sales"] * 100)
def test_orders_are_distinct_not_lines(db):
    from sqlalchemy import select, func
    from app.models import Order
    lines = db.scalar(select(func.count()).select_from(Order)); assert sv._totals(db)["invoices"] < lines
def test_date_bounds_inclusive_and_trend_reconciles(db):
    s, e = date(2025, 1, 1), date(2025, 12, 31)
    t = sv._totals(db, start=s, end=e)
    assert sum(m["sales"] for m in sv.sales_trend(db, s, e)) == pytest.approx(t["sales"])
    assert sum(r["sales"] for r in sv.regions(db, s, e)) == pytest.approx(t["sales"])
def test_filter_and_empty(db):
    assert sv._totals(db, region="West")["sales"] < sv._totals(db)["sales"]
    z = sv._totals(db, start=date(1990, 1, 1), end=date(1990, 1, 2)); assert z["gross_margin_pct"] == 0 and z["average_invoice_value"] == 0
def test_growth_unavailable_when_no_prior(db):
    assert sv.overview(db, date(2024, 1, 1), date(2024, 3, 31))["growth_pct"]["sales"] is None

def test_seed_uses_indian_bike_spares_data(db):
    from sqlalchemy import select
    from app.models import Product, Region
    categories = set(db.scalars(select(Product.category)).all())
    countries = set(db.scalars(select(Region.country)).all())
    assert "Engine & Filtration" in categories
    assert "Drive & Transmission" in categories
    assert countries == {"India"}

def test_sidebar_reports_return_filtered_business_data(db):
    parts = sv.parts(db, start=date(2025, 1, 1), end=date(2025, 12, 31), region="West")
    discounts = sv.discounts(db, start=date(2025, 1, 1), end=date(2025, 12, 31), region="West")
    dealers = sv.dealers(db, start=date(2025, 1, 1), end=date(2025, 12, 31), region="West")
    invoices = sv.invoices(db, start=date(2025, 1, 1), end=date(2025, 12, 31), region="West")
    assert parts and parts[0]["part_name"] and parts[0]["sales"] > 0
    assert discounts and 0 <= discounts[0]["discount_pct"] <= 15
    assert dealers and dealers[0]["region"] == "West"
    assert invoices and invoices[0]["region"] == "West"
