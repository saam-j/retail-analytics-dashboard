# Retail Analytics Dashboard
FastAPI + SQLAlchemy (PostgreSQL) backend, React/Vite/Tailwind/Recharts frontend. Data is **synthetic demo data**.
## Run
    createdb retail
    cd backend && cp .env.example .env && pip install -r requirements.txt
    export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/retail
    python -m app.seed && uvicorn app.main:app --reload      # API docs: /docs
    cd frontend && npm install && npm run dev                # http://localhost:5173
    cd backend && pytest
## Definitions
- `orders` grain = order LINE; orders KPI = COUNT(DISTINCT order_id).
- Revenue = `sales_amount` (already after discount); profit = sales - cost; discount is a fraction 0..1.
- Margin = SUM(profit)/SUM(revenue). Growth compares the equal-length period immediately before the range; `null` = unavailable.
- YTD = Jan 1 of the end-date year through end date (inclusive).
