"""Deterministic SYNTHETIC demo data (not real business performance). `python -m app.seed`"""
import random
from datetime import date, timedelta
from decimal import Decimal as D
from sqlalchemy import select
from .db import Base, engine, SessionLocal
from .models import *
REGIONS = ["West", "East", "Central", "South"]
CATS = {"Technology": ["Phones", "Accessories"], "Furniture": ["Chairs", "Tables"], "Office Supplies": ["Paper", "Binders"]}
SEGS = ["Consumer", "Corporate", "Home Office"]
def q(x): return D(x).quantize(D("0.01"))
def seed(s, n_orders=900, start=date(2024, 1, 1), end=date(2026, 9, 30)):
    r = random.Random(42)
    for i, n in enumerate(REGIONS, 1):
        s.add(Region(region_id=i, region_name=n, country="USA"))
    s.flush()
    prods = []
    for c, subs in CATS.items():
        for sub in subs:
            for k in range(3):
                price = r.uniform(15, 900) if c != "Office Supplies" else r.uniform(5, 80)
                p = Product(product_id=f"P{len(prods)+1:03}", product_name=f"{sub} {k+1}", category=c,
                            subcategory=sub, unit_cost=q(price * r.uniform(0.55, 0.9)))
                p._price = price
                prods.append(p)
                s.add(p)
    s.flush()
    custs = [Customer(customer_id=f"C{i:03}", customer_name=f"Customer {i}", customer_segment=r.choice(SEGS),
                      city="Demo City", state="Demo State", region_id=r.randint(1, 4)) for i in range(1, 61)]
    s.add_all(custs)
    s.flush()
    span = (end - start).days
    for n in range(1, n_orders + 1):
        c = r.choice(custs)
        d = start + timedelta(days=r.randint(0, span))
        for _ in range(r.randint(1, 3)):
            p = r.choice(prods)
            qty = r.randint(1, 6)
            disc = r.choice([0, 0, 0, .1, .2, .3, .4])
            price = q(p._price)
            sales = q(price * qty * (1 - D(str(disc))))
            cost = q(p.unit_cost * qty)
            s.add(Order(order_id=f"O{n:05}", order_date=d, customer_id=c.customer_id, product_id=p.product_id,
                        region_id=c.region_id, quantity=qty, unit_price=price, discount=D(str(disc)),
                        sales_amount=sales, cost_amount=cost, profit=sales - cost))
    s.commit()
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        models = (Region, Customer, Product, Order)
        if any(s.scalar(select(model).limit(1)) is not None for model in models):
            raise SystemExit("Refusing to seed a database that already contains application data.")
        seed(s)
    print("Seeded synthetic demo data.")
