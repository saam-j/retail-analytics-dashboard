# Retail Analytics Dashboard

FastAPI and SQLAlchemy backend, PostgreSQL database, and React/Vite frontend. The seed script generates **synthetic Indian motorcycle spare-parts sales data** with prices in INR. It is demo data, not real business performance.

## Prerequisites

Install Python 3.10+, Node.js/npm, and PostgreSQL. Open PowerShell in the project folder and check that they are available:

```powershell
py --version
node --version
npm --version
Get-Service -Name 'postgresql*'
```

Make sure the PostgreSQL service is running. If `psql` is not on `PATH`, use SQL Shell (psql) or pgAdmin for the database steps below.

## Create the database

Use your own PostgreSQL role and password; the example credentials in `backend\.env.example` may not match your installation. Check whether the database already exists:

```powershell
psql -U YOUR_POSTGRES_USER -d postgres -c "SELECT datname FROM pg_database WHERE datname = 'retail';"
```

If the query returns no row, create it:

```powershell
psql -U YOUR_POSTGRES_USER -d postgres -c "CREATE DATABASE retail;"
```

`psql` prompts for the password. Do not put the password in the command. In pgAdmin, the equivalent is to create a database named `retail` using your connected server role.

## Configure and start the backend

In the first VS Code terminal, from the project folder:

```powershell
Set-Location .\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

In `.env`, set `DATABASE_URL` to the credentials and database you just verified. For example, replace the placeholders with your local values:

```text
DATABASE_URL=postgresql+psycopg://YOUR_POSTGRES_USER:YOUR_POSTGRES_PASSWORD@localhost:5432/retail
CORS_ORIGINS=http://localhost:5173
```

If the password contains URL-reserved characters, percent-encode them in the URL. Save `.env`, then continue in the same terminal:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$databaseUrl = (Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1).Substring('DATABASE_URL='.Length)
$env:DATABASE_URL = $databaseUrl
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The seed command creates the tables and inserts sample rows only when the application tables are empty. It refuses to seed a database that already has application data; it does not delete or reset existing data. Leave this terminal running. Check the API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health).

## Start the frontend

Open a second VS Code terminal, from the project folder:

```powershell
Set-Location .\frontend
npm install
npm run dev
```

Open the dashboard at [http://localhost:5173](http://localhost:5173). Vite proxies `/api` requests to the backend on port 8000.

## Verify the application

With the backend running, these commands should return a healthy status and available database filters:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/filters
```

Run the backend tests from a third terminal at the project folder:

```powershell
Set-Location .
.\backend\.venv\Scripts\python.exe -m pytest backend
```

Check the frontend production build from the project folder:

```powershell
npm run build --prefix frontend
```

## Definitions

- One row in `orders` is an invoice line; the invoice count is `COUNT(DISTINCT order_id)`.
- `sales_amount` is parts sales after discount. Gross profit is sales minus cost; discount is a fraction from 0 to 1. Monetary values are Indian rupees (INR).
- Gross margin is total gross profit divided by total parts sales. Growth compares the selected period with the equal-length period immediately before it; `null` means there is no prior period to compare.
- YTD runs from January 1 of the selected end date's year through that end date, inclusive.
