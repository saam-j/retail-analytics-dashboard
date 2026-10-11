"""Deterministic SYNTHETIC demo data (not real business performance). `python -m app.seed`"""
import random
from datetime import date, timedelta
from decimal import Decimal as D
from sqlalchemy import select
from .db import Base, engine, SessionLocal
from .models import *
REGIONS = ["North", "South", "East", "West", "Central"]
CATS = {
    "Engine & Filtration": ["Spark Plug", "Air Filter", "Oil Filter", "Engine Gasket Set"],
    "Brakes": ["Front Brake Pads", "Rear Brake Shoes", "Brake Disc Rotor", "Brake Cable"],
    "Drive & Transmission": ["Drive Chain Kit", "Front Sprocket", "Rear Sprocket", "Clutch Plate Set"],
    "Electrical": ["Headlamp Assembly", "12V Battery", "Ignition Coil", "Indicator Set"],
    "Suspension & Controls": ["Front Fork Seal Kit", "Rear Shock Absorber", "Clutch Lever", "Throttle Cable"],
    "Service & Lubricants": ["Engine Oil 1L", "Chain Lubricant", "Brake Fluid 500ml", "Coolant 1L"],
}
PRICE_RANGES = {
    "Engine & Filtration": (120, 4200),
    "Brakes": (90, 6800),
    "Drive & Transmission": (150, 9500),
    "Electrical": (180, 12500),
    "Suspension & Controls": (100, 14800),
    "Service & Lubricants": (160, 1100),
}
SEGS = ["Authorized Dealer", "Independent Workshop", "Retail Parts Shop"]
LOCATIONS = [
    ("Delhi", "Delhi", "North"), ("Jaipur", "Rajasthan", "North"), ("Lucknow", "Uttar Pradesh", "North"),
    ("Chandigarh", "Punjab", "North"), ("Bengaluru", "Karnataka", "South"),
    ("Chennai", "Tamil Nadu", "South"), ("Hyderabad", "Telangana", "South"),
    ("Kochi", "Kerala", "South"), ("Kolkata", "West Bengal", "East"),
    ("Bhubaneswar", "Odisha", "East"), ("Patna", "Bihar", "East"),
    ("Mumbai", "Maharashtra", "West"), ("Pune", "Maharashtra", "West"),
    ("Ahmedabad", "Gujarat", "West"), ("Bhopal", "Madhya Pradesh", "Central"),
    ("Raipur", "Chhattisgarh", "Central"),
]
def q(x): return D(x).quantize(D("0.01"))
def seed(s, n_orders=900, start=date(2024, 1, 1), end=date(2026, 9, 30)):
    r = random.Random(42)
    region_ids = {name: i for i, name in enumerate(REGIONS, 1)}
    for i, name in enumerate(REGIONS, 1):
        s.add(Region(region_id=i, region_name=name, country="India"))
    s.flush()
    prods = []
    for category, parts in CATS.items():
        low, high = PRICE_RANGES[category]
        for part_name in parts:
            for variant in range(1, 4):
                price = r.uniform(low, high)
                part = Product(product_id=f"BP{len(prods)+1:03}", product_name=f"{part_name} - Variant {variant}",
                               category=category, subcategory=part_name, unit_cost=q(price * r.uniform(0.55, 0.82)))
                part._price = price
                prods.append(part)
                s.add(part)
    s.flush()
    custs = []
    for i in range(1, 61):
        city, state, region = r.choice(LOCATIONS)
        custs.append(Customer(customer_id=f"DLR{i:03}", customer_name=f"{r.choice(['Shree Balaji', 'Metro Moto', 'Highway Auto', 'Sai Motors', 'Prime Riders'])} Spares {i}",
                              customer_segment=r.choice(SEGS), city=city, state=state, region_id=region_ids[region]))
    s.add_all(custs)
    s.flush()
    span = (end - start).days
    for n in range(1, n_orders + 1):
        c = r.choice(custs)
        d = start + timedelta(days=r.randint(0, span))
        for _ in range(r.randint(1, 5)):
            p = r.choice(prods)
            qty = r.randint(1, 12)
            disc = r.choice([0, 0, 0, .03, .05, .08, .1, .15])
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
