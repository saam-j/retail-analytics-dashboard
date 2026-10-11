import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { LayoutDashboard, Package, Globe2, Percent, Users, ShoppingCart } from "lucide-react";
import { Filters, get } from "./api";
type Ov = { revenue: number; profit: number; margin_pct: number; orders: number; aov: number; ytd_sales?: number; growth_pct?: Record<string, number | null> };
const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
function useApi<T>(path: string, f: Filters) {
  const [s, set] = useState<{ data?: T; error?: string; loading: boolean }>({ loading: true });
  useEffect(() => { const c = new AbortController(); set(p => ({ ...p, loading: true, error: undefined }));
    get<T>(path, f, c.signal).then(data => set({ data, loading: false })).catch(e => e.name !== "AbortError" && set({ error: e.message, loading: false }));
    return () => c.abort(); }, [path, JSON.stringify(f)]);
  return s;
}
const Card = ({ t, children }: { t: string; children: React.ReactNode }) => <section className="bg-white rounded-xl border border-zinc-200 p-4"><h2 className="font-semibold mb-3">{t}</h2>{children}</section>;
const State = ({ s, children }: { s: { loading: boolean; error?: string; data?: any }; children: React.ReactNode }) =>
  s.error ? <p role="alert" className="text-red-600 text-sm">{s.error}</p> : !s.data ? <p className="text-sm text-zinc-500">Loading…</p> : Array.isArray(s.data) && !s.data.length ? <p className="text-sm text-zinc-500">No data for these filters.</p> : <>{children}</>;
export default function App() {
  const init = Object.fromEntries(new URLSearchParams(location.search));
  const [f, setF] = useState<Filters>({ start: "2025-01-01", end: "2026-09-30", region: "", category: "", segment: "", ...init });
  useEffect(() => { history.replaceState(null, "", "?" + new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString()); }, [f]);
  const opts = useApi<{ regions: string[]; categories: string[]; segments: string[] }>("/filters", {} as Filters);
  const ov = useApi<Ov>("/analytics/overview", f), tr = useApi<any[]>("/analytics/sales-trend", f), rg = useApi<any[]>("/analytics/regions", f);
  const sel = (k: keyof Filters, list: string[] = []) => <select aria-label={k} className="border rounded-md px-2 py-1 text-sm bg-white" value={f[k]} onChange={e => setF({ ...f, [k]: e.target.value })}><option value="">All {k}s</option>{list.map(x => <option key={x}>{x}</option>)}</select>;
  const g = ov.data?.growth_pct;
  const kpis: [string, string, string, any][] = ov.data ? [["Revenue", money(ov.data.revenue), "revenue", Package], ["Profit", money(ov.data.profit), "profit", Percent], ["Margin", ov.data.margin_pct.toFixed(1) + "%", "", Percent], ["YTD Sales", money(ov.data.ytd_sales ?? 0), "", Globe2], ["Orders", String(ov.data.orders), "orders", ShoppingCart], ["Avg Order", money(ov.data.aov), "aov", Users]] : [];
  return <div className="flex min-h-screen">
    <aside className="hidden md:flex w-56 bg-ink text-zinc-300 flex-col p-4 gap-2"><div className="text-brand font-bold text-xl mb-4">Retail IQ</div>
      {["Overview", "Sales", "Products", "Regions", "Discounts", "Customers", "Orders"].map((n, i) => <a key={n} href="#" className={`px-3 py-2 rounded-md text-sm flex gap-2 items-center ${i === 0 ? "text-brand bg-white/10" : ""}`}><LayoutDashboard size={16} />{n}</a>)}</aside>
    <main className="flex-1 p-4 md:p-6 space-y-4">
      <header className="flex flex-wrap gap-2 items-center justify-between"><div><h1 className="text-2xl font-semibold">Sales Overview</h1><p className="text-sm text-zinc-500">Synthetic demo data · revenue is after discount</p></div>
        <div className="flex flex-wrap gap-2"><input type="date" aria-label="start" className="border rounded-md px-2 py-1 text-sm" value={f.start} onChange={e => setF({ ...f, start: e.target.value })} /><input type="date" aria-label="end" className="border rounded-md px-2 py-1 text-sm" value={f.end} onChange={e => setF({ ...f, end: e.target.value })} />
          {sel("region", opts.data?.regions)}{sel("category", opts.data?.categories)}{sel("segment", opts.data?.segments)}
          <button className="text-sm px-3 py-1 rounded-md bg-brand/20" onClick={() => setF({ ...f, region: "", category: "", segment: "" })}>Clear</button></div></header>
      <State s={ov}><div className="grid grid-cols-2 lg:grid-cols-6 gap-3">{kpis.map(([t, v, k]) => { const d = k && g ? g[k] : null; return <div key={t} className="bg-white rounded-xl border p-3"><div className="text-xs text-zinc-500">{t}</div><div className="text-xl font-bold">{v}</div>
        {k && <div className={`text-xs ${d == null ? "text-zinc-400" : d >= 0 ? "text-green-600" : "text-red-500"}`}>{d == null ? "comparison unavailable" : `${d >= 0 ? "▲" : "▼"} ${Math.abs(d).toFixed(1)}% vs prev period`}</div>}</div>; })}</div></State>
      <div className="grid lg:grid-cols-3 gap-4"><div className="lg:col-span-2"><Card t="Sales Trend"><State s={tr}><ResponsiveContainer height={280}><AreaChart data={tr.data}><CartesianGrid vertical={false} stroke="#eee" /><XAxis dataKey="month" fontSize={11} /><YAxis fontSize={11} tickFormatter={v => `${v / 1000}k`} /><Tooltip formatter={(v: number) => money(v)} />
        <Area dataKey="revenue" stroke="#F2B705" fill="#F2B70540" strokeWidth={2} /><Area dataKey="profit" stroke="#ef6b5b" fill="transparent" strokeWidth={2} /></AreaChart></ResponsiveContainer></State></Card></div>
        <Card t="Regions (click to filter)"><State s={rg}><ResponsiveContainer height={280}><BarChart data={rg.data} layout="vertical"><XAxis type="number" fontSize={11} tickFormatter={v => `${v / 1000}k`} /><YAxis type="category" dataKey="region" fontSize={11} width={60} /><Tooltip formatter={(v: number) => money(v)} />
          <Bar dataKey="revenue" fill="#F2B705" cursor="pointer" onClick={(d: any) => setF({ ...f, region: d.region })} /><Bar dataKey="profit" fill="#fbe3a0" /></BarChart></ResponsiveContainer>
          <p className="text-xs text-zinc-500 mt-2">Weak margin: {rg.data?.filter(r => r.weak_profitability).map(r => r.region).join(", ") || "none"}</p></State></Card></div>
    </main></div>;
}
