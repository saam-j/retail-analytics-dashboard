import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/retail")
engine = create_engine(URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
def get_db():
    with SessionLocal() as s: yield s
