import os
from datetime import date
from typing import Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, distinct
from sqlalchemy.exc import SQLAlchemyError
from .db import get_db
from . import services as sv
from .models import Region, Product, Customer
app = FastAPI(title="Retail Analytics API")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["GET"], allow_headers=["*"])
def params(start: Optional[date] = None, end: Optional[date] = None, region: Optional[str] = None,
           category: Optional[str] = None, segment: Optional[str] = None):
    if start and end and start > end: raise HTTPException(422, "start must be <= end")
    return dict(start=start, end=end, region=region, category=category, segment=segment)
@app.exception_handler(SQLAlchemyError)
async def db_err(_, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": "Database error"}, status_code=503)
@app.get("/api/health")
def health(): return {"status": "ok"}
@app.get("/api/filters")
def filters(db=Depends(get_db)):
    return {"regions": db.scalars(select(Region.region_name).order_by(Region.region_name)).all(),
            "categories": db.scalars(select(distinct(Product.category)).order_by(Product.category)).all(),
            "segments": db.scalars(select(distinct(Customer.customer_segment)).order_by(Customer.customer_segment)).all()}
@app.get("/api/analytics/overview")
def overview(p=Depends(params), db=Depends(get_db)): return sv.overview(db, **p)
@app.get("/api/analytics/sales-trend")
def trend(p=Depends(params), db=Depends(get_db)): return sv.sales_trend(db, **p)
@app.get("/api/analytics/regions")
def regions(p=Depends(params), db=Depends(get_db)): return sv.regions(db, **p)
