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
    sales, gross_profit, invoices = _f(row[0]), _f(row[1]), row[2]
    return {"sales": sales, "gross_profit": gross_profit,
            "gross_margin_pct": gross_profit / sales * 100 if sales else 0.0,
            "invoices": invoices, "average_invoice_value": sales / invoices if invoices else 0.0}
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
        metrics = ("sales", "gross_profit", "invoices", "average_invoice_value")
        out["growth_pct"] = {key: growth(cur[key], prev[key]) if prev["invoices"] else None for key in metrics}
    if end:
        out["ytd_sales"] = _totals(db, start=date(end.year, 1, 1), end=end, **f)["sales"]
        py = _totals(db, start=date(end.year - 1, 1, 1), end=date(end.year - 1, end.month, min(end.day, 28)), **f)
        out["ytd_growth_pct"] = growth(out["ytd_sales"], py["sales"]) if py["invoices"] else None
    return out
def month_expr(db):
    return func.strftime("%Y-%m", Order.order_date) if db.bind.dialect.name == "sqlite" else func.to_char(Order.order_date, "YYYY-MM")
def sales_trend(db, start, end, **f):
    m = month_expr(db)
    rows = db.execute(filtered(select(m, func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order), start=start, end=end, **f)
                      .group_by(m).order_by(m)).all()
    return [{"month": a, "sales": _f(b), "gross_profit": _f(c)} for a, b, c in rows]
def regions(db, start, end, **f):
    rows = db.execute(filtered(select(Region.region_name, func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f).group_by(Region.region_name)).all()
    res = [{"region": n, "sales": _f(r), "gross_profit": _f(p),
            "gross_margin_pct": _f(p) / _f(r) * 100 if r else 0} for n, r, p in rows]
    res.sort(key=lambda x: -x["sales"])
    avg = sum(x["gross_margin_pct"] for x in res) / len(res) if res else 0
    for x in res: x["below_average_margin"] = x["gross_margin_pct"] < avg
    return res

def parts(db, start=None, end=None, **f):
    rows = db.execute(filtered(select(Product.product_id, Product.product_name, Product.category, Product.subcategory,
                                      func.sum(Order.quantity), func.count(func.distinct(Order.order_id)),
                                      func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f)
                      .group_by(Product.product_id, Product.product_name, Product.category, Product.subcategory)
                      .order_by(func.sum(Order.sales_amount).desc()).limit(100)).all()
    return [{"part_id": pid, "part_name": name, "category": category, "part_type": part_type,
             "units_sold": quantity, "invoices": invoices, "sales": _f(sales), "gross_profit": _f(profit)}
            for pid, name, category, part_type, quantity, invoices, sales, profit in rows]

def discounts(db, start=None, end=None, **f):
    rows = db.execute(filtered(select(Order.discount, func.count(Order.line_id), func.sum(Order.quantity),
                                      func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f)
                      .group_by(Order.discount).order_by(Order.discount)).all()
    return [{"discount_pct": _f(discount) * 100, "invoice_lines": lines, "units_sold": quantity,
             "sales": _f(sales), "gross_profit": _f(profit)}
            for discount, lines, quantity, sales, profit in rows]

def dealers(db, start=None, end=None, **f):
    rows = db.execute(filtered(select(Customer.customer_id, Customer.customer_name, Customer.customer_segment,
                                      Customer.city, Customer.state, Region.region_name,
                                      func.count(func.distinct(Order.order_id)), func.sum(Order.quantity),
                                      func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f)
                      .group_by(Customer.customer_id, Customer.customer_name, Customer.customer_segment,
                                Customer.city, Customer.state, Region.region_name)
                      .order_by(func.sum(Order.sales_amount).desc()).limit(100)).all()
    return [{"dealer_id": dealer_id, "dealer_name": name, "customer_type": segment, "city": city,
             "state": state, "region": region, "invoices": invoices, "units_sold": quantity,
             "sales": _f(sales), "gross_profit": _f(profit)}
            for dealer_id, name, segment, city, state, region, invoices, quantity, sales, profit in rows]

def invoices(db, start=None, end=None, **f):
    rows = db.execute(filtered(select(Order.order_id, Order.order_date, Customer.customer_name, Customer.city,
                                      Customer.state, Region.region_name, Order.order_status,
                                      func.count(Order.line_id), func.sum(Order.quantity),
                                      func.sum(Order.sales_amount), func.sum(Order.profit)).select_from(Order),
                               start=start, end=end, **f)
                      .group_by(Order.order_id, Order.order_date, Customer.customer_name, Customer.city,
                                Customer.state, Region.region_name, Order.order_status)
                      .order_by(Order.order_date.desc(), Order.order_id.desc()).limit(100)).all()
    return [{"invoice_id": invoice_id, "invoice_date": invoice_date.isoformat(), "dealer_name": dealer,
             "city": city, "state": state, "region": region, "status": status, "line_items": lines,
             "units": quantity, "sales": _f(sales), "gross_profit": _f(profit)}
            for invoice_id, invoice_date, dealer, city, state, region, status, lines, quantity, sales, profit in rows]
