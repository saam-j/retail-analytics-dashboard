from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from .models import Order, Product, Customer, Region
def _f(v): return float(v or 0)
def filtered(stmt, start=None, end=None, region=None, category=None, segment=None):
    stmt = stmt.join(Product, Product.product_id == Order.product_id).join(Customer, Customer.customer_id == Order.customer_id)\
               .join(Region, Region.region_id == Order.region_id)
    if start: stmt = stmt.where(Order.order_date >= start)
    if end: stmt = stmt.where(Order.order_date <= end)  # inclusive
    if region: stmt = stmt.where(Region.region_name == region)
    if category: stmt = stmt.where(Product.category == category)
    if segment: stmt = stmt.where(Customer.customer_segment == segment)
    return stmt
def _totals(db, **f):
    row = db.execute(filtered(select(func.sum(Order.sales_amount), func.sum(Order.profit),
                                     func.count(func.distinct(Order.order_id))).select_from(Order), **f)).one()
    rev, prof, n = _f(row[0]), _f(row[1]), row[2]
    return {"revenue": rev, "profit": prof, "margin_pct": prof / rev * 100 if rev else 0.0, "orders": n, "aov": rev / n if n else 0.0}
def growth(cur, prev):
    return None if not prev else (cur - prev) / prev * 100  # None = comparison unavailable
def overview(db, start, end, **f):
    cur = _totals(db, start=start, end=end, **f)
    out = dict(cur)
    if start and end:
        days = (end - start).days + 1
        pe, ps = start - timedelta(days=1), start - timedelta(days=days)
        prev = _totals(db, start=ps, end=pe, **f)  # equal-length period immediately before
        out["comparison_period"] = [ps.isoformat(), pe.isoformat()]
        out["growth_pct"] = {k: growth(cur[k], prev[k]) if prev["orders"] else None for k in ("revenue", "profit", "orders", "aov")}
    if end:
        out["ytd_sales"] = _totals(db, start=date(end.year, 1, 1), end=end, **f)["revenue"]
        py = _totals(db, start=date(end.year - 1, 1, 1), end=date(end.year - 1, end.month, min(end.day, 28)), **f)
        out["ytd_growth_pct"] = growth(out["ytd_sales"], py["revenue"]) if py["orders"] else None
    return out
def month_expr(db):
    return func.strftime("%Y-%m", Order.order_date) if db.bind.dialect.name == "sqlite" else func.to_char(Order.order_date, "YYYY-MM")
def sales_trend(db, start, end, **f):
    m = month_expr(db)
    rows = db.execute(filtered(select(m, func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order), start=start, end=end, **f)
                      .group_by(m).order_by(m)).all()
    return [{"month": a, "revenue": _f(b), "profit": _f(c)} for a, b, c in rows]
def regions(db, start, end, **f):
    rows = db.execute(filtered(select(Region.region_name, func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f).group_by(Region.region_name)).all()
    res = [{"region": n, "revenue": _f(r), "profit": _f(p), "margin_pct": _f(p) / _f(r) * 100 if r else 0} for n, r, p in rows]
    res.sort(key=lambda x: -x["revenue"])
    avg = sum(x["margin_pct"] for x in res) / len(res) if res else 0
    for x in res: x["weak_profitability"] = x["margin_pct"] < avg
    return res
