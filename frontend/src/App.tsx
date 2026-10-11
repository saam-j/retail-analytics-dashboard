import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { LayoutDashboard, Package, Globe2, Percent, Users, ShoppingCart, TrendingUp } from "lucide-react";
import { Filters, get } from "./api";
type Ov = { sales: number; gross_profit: number; gross_margin_pct: number; invoices: number; average_invoice_value: number; ytd_sales?: number; growth_pct?: Record<string, number | null> };
type Section = "overview" | "parts-sales" | "spare-parts" | "regions" | "discounts" | "dealers" | "invoices";
type PartRow = { part_id: string; part_name: string; category: string; part_type: string; units_sold: number; invoices: number; sales: number; gross_profit: number };
type DiscountRow = { discount_pct: number; invoice_lines: number; units_sold: number; sales: number; gross_profit: number };
type DealerRow = { dealer_id: string; dealer_name: string; customer_type: string; city: string; state: string; region: string; invoices: number; units_sold: number; sales: number; gross_profit: number };
type InvoiceRow = { invoice_id: string; invoice_date: string; dealer_name: string; city: string; state: string; region: string; status: string; line_items: number; units: number; sales: number; gross_profit: number };
const money = (n: number) => n.toLocaleString("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const sections: { id: Section; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "parts-sales", label: "Parts Sales", icon: TrendingUp },
  { id: "spare-parts", label: "Spare Parts", icon: Package },
  { id: "regions", label: "Regions", icon: Globe2 },
  { id: "discounts", label: "Discounts", icon: Percent },
  { id: "dealers", label: "Dealers", icon: Users },
  { id: "invoices", label: "Invoices", icon: ShoppingCart },
];
const sectionTitles: Record<Section, string> = {
  overview: "Bike Spares Sales", "parts-sales": "Parts Sales", "spare-parts": "Spare Parts",
  regions: "Sales by Region", discounts: "Discount Analysis", dealers: "Dealer Sales", invoices: "Invoices",
};
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
function ReportTable<T extends object>({ rows, columns }: { rows: T[]; columns: { label: string; key: keyof T; money?: boolean }[] }) {
  return <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead className="border-b text-xs uppercase text-zinc-500"><tr>{columns.map(column => <th key={column.label} className="px-3 py-2 font-medium">{column.label}</th>)}</tr></thead>
    <tbody className="divide-y">{rows.map((row, index) => <tr key={index} className="hover:bg-zinc-50">{columns.map(column => {
      const value = row[column.key];
      return <td key={column.label} className="px-3 py-2 whitespace-nowrap">{column.money && typeof value === "number" ? money(value) : String(value ?? "-")}</td>;
    })}</tr>)}</tbody></table></div>;
}
export default function App() {
  const init = Object.fromEntries(new URLSearchParams(location.search));
  const [f, setF] = useState<Filters>({ start: "2025-01-01", end: "2026-09-30", region: "", category: "", segment: "", ...init });
  const initialSection = sections.find(item => item.id === location.hash.slice(1))?.id ?? "overview";
  const [section, setSection] = useState<Section>(initialSection);
  useEffect(() => { history.replaceState(null, "", "?" + new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString() + `#${section}`); }, [f, section]);
  const opts = useApi<{ regions: string[]; categories: string[]; segments: string[] }>("/filters", {} as Filters);
  const ov = useApi<Ov>("/analytics/overview", f), tr = useApi<any[]>("/analytics/sales-trend", f), rg = useApi<any[]>("/analytics/regions", f);
  const partRows = useApi<PartRow[]>("/analytics/parts", f), discountRows = useApi<DiscountRow[]>("/analytics/discounts", f);
  const dealerRows = useApi<DealerRow[]>("/analytics/dealers", f), invoiceRows = useApi<InvoiceRow[]>("/analytics/invoices", f);
  const sel = (k: keyof Filters, label: string, list: string[] = []) => {
    const allLabel = label === "Part category" ? "All part categories" : label === "Customer type" ? "All customer types" : "All regions";
    return <select aria-label={label} className="border rounded-md px-2 py-1 text-sm bg-white" value={f[k]} onChange={e => setF({ ...f, [k]: e.target.value })}><option value="">{allLabel}</option>{list.map(x => <option key={x}>{x}</option>)}</select>;
  };
  const g = ov.data?.growth_pct;
  const kpis: [string, string, string, any][] = ov.data ? [["Parts Sales", money(ov.data.sales), "sales", Package], ["Gross Profit", money(ov.data.gross_profit), "gross_profit", Percent], ["Gross Margin", ov.data.gross_margin_pct.toFixed(1) + "%", "", Percent], ["YTD Sales", money(ov.data.ytd_sales ?? 0), "", Globe2], ["Invoices", String(ov.data.invoices), "invoices", ShoppingCart], ["Avg Invoice Value", money(ov.data.average_invoice_value), "average_invoice_value", Users]] : [];
  return <div className="flex min-h-screen">
    <aside className="hidden md:flex w-56 bg-ink text-zinc-300 flex-col p-4 gap-2"><div className="text-brand font-bold text-xl mb-4">Retail IQ</div>
      <nav aria-label="Main navigation" className="flex flex-col gap-1">{sections.map(item => { const Icon = item.icon; return <button key={item.id} type="button" aria-current={section === item.id ? "page" : undefined} onClick={() => setSection(item.id)} className={`px-3 py-2 rounded-md text-sm flex gap-2 items-center text-left ${section === item.id ? "text-brand bg-white/10" : "hover:bg-white/5"}`}><Icon size={16} />{item.label}</button>; })}</nav></aside>
    <main className="flex-1 p-4 md:p-6 space-y-4">
      <header className="flex flex-wrap gap-2 items-center justify-between"><div><h1 className="text-2xl font-semibold">{sectionTitles[section]}</h1><p className="text-sm text-zinc-500">Synthetic India dealer data · prices in INR</p></div>
        <div className="flex flex-wrap gap-2"><input type="date" aria-label="start" className="border rounded-md px-2 py-1 text-sm" value={f.start} onChange={e => setF({ ...f, start: e.target.value })} /><input type="date" aria-label="end" className="border rounded-md px-2 py-1 text-sm" value={f.end} onChange={e => setF({ ...f, end: e.target.value })} />
          {sel("region", "Region", opts.data?.regions)}{sel("category", "Part category", opts.data?.categories)}{sel("segment", "Customer type", opts.data?.segments)}
          <button className="text-sm px-3 py-1 rounded-md bg-brand/20" onClick={() => setF({ ...f, region: "", category: "", segment: "" })}>Clear</button></div></header>
      {section === "overview" && <>
        <State s={ov}><div className="grid grid-cols-2 lg:grid-cols-6 gap-3">{kpis.map(([t, v, k]) => { const d = k && g ? g[k] : null; return <div key={t} className="bg-white rounded-xl border p-3"><div className="text-xs text-zinc-500">{t}</div><div className="text-xl font-bold">{v}</div>
          {k && <div className={`text-xs ${d == null ? "text-zinc-400" : d >= 0 ? "text-green-600" : "text-red-500"}`}>{d == null ? "comparison unavailable" : `${d >= 0 ? "▲" : "▼"} ${Math.abs(d).toFixed(1)}% vs prev period`}</div>}</div>; })}</div></State>
        <div className="grid lg:grid-cols-3 gap-4"><div className="lg:col-span-2"><Card t="Monthly Parts Sales & Gross Profit"><State s={tr}><ResponsiveContainer height={280}><AreaChart data={tr.data}><CartesianGrid vertical={false} stroke="#eee" /><XAxis dataKey="month" fontSize={11} /><YAxis fontSize={11} tickFormatter={v => `₹${v / 1000}k`} /><Tooltip formatter={(v: number) => money(v)} />
          <Area dataKey="sales" name="Parts sales" stroke="#F2B705" fill="#F2B70540" strokeWidth={2} /><Area dataKey="gross_profit" name="Gross profit" stroke="#ef6b5b" fill="transparent" strokeWidth={2} /></AreaChart></ResponsiveContainer></State></Card></div>
          <Card t="Sales by Region"><State s={rg}><ResponsiveContainer height={280}><BarChart data={rg.data} layout="vertical"><XAxis type="number" fontSize={11} tickFormatter={v => `₹${v / 1000}k`} /><YAxis type="category" dataKey="region" fontSize={11} width={60} /><Tooltip formatter={(v: number) => money(v)} />
            <Bar dataKey="sales" name="Parts sales" fill="#F2B705" cursor="pointer" onClick={(d: any) => { setF({ ...f, region: d.region }); setSection("regions"); }} /><Bar dataKey="gross_profit" name="Gross profit" fill="#fbe3a0" /></BarChart></ResponsiveContainer>
            <p className="text-xs text-zinc-500 mt-2">Below-average gross margin: {rg.data?.filter(r => r.below_average_margin).map(r => r.region).join(", ") || "none"}</p></State></Card></div>
      </>}
      {section === "parts-sales" && <><State s={ov}><div className="grid grid-cols-2 lg:grid-cols-4 gap-3">{kpis.filter(([, , key]) => key).map(([label, value]) => <div key={label} className="bg-white rounded-lg border p-3"><div className="text-xs text-zinc-500">{label}</div><div className="text-xl font-bold">{value}</div></div>)}</div></State><Card t="Monthly Parts Sales & Gross Profit"><State s={tr}><ResponsiveContainer height={360}><AreaChart data={tr.data}><CartesianGrid vertical={false} stroke="#eee" /><XAxis dataKey="month" fontSize={11} /><YAxis fontSize={11} tickFormatter={v => `₹${v / 1000}k`} /><Tooltip formatter={(v: number) => money(v)} /><Area dataKey="sales" name="Parts sales" stroke="#F2B705" fill="#F2B70540" strokeWidth={2} /><Area dataKey="gross_profit" name="Gross profit" stroke="#ef6b5b" fill="transparent" strokeWidth={2} /></AreaChart></ResponsiveContainer></State></Card></>}
      {section === "spare-parts" && <Card t="Top Spare Parts"><State s={partRows}><ReportTable rows={partRows.data!} columns={[{ label: "Part", key: "part_name" }, { label: "Category", key: "category" }, { label: "Part type", key: "part_type" }, { label: "Units sold", key: "units_sold" }, { label: "Invoices", key: "invoices" }, { label: "Sales", key: "sales", money: true }, { label: "Gross profit", key: "gross_profit", money: true }]} /></State></Card>}
      {section === "regions" && <Card t="Regional Parts Sales"><State s={rg}><div className="h-[420px]"><ResponsiveContainer><BarChart data={rg.data} layout="vertical"><CartesianGrid horizontal={false} stroke="#eee" /><XAxis type="number" fontSize={11} tickFormatter={v => money(v)} /><YAxis type="category" dataKey="region" fontSize={12} width={80} /><Tooltip formatter={(v: number) => money(v)} /><Bar dataKey="sales" name="Parts sales" fill="#F2B705" /><Bar dataKey="gross_profit" name="Gross profit" fill="#ef6b5b" /></BarChart></ResponsiveContainer></div><ReportTable rows={rg.data!} columns={[{ label: "Region", key: "region" }, { label: "Sales", key: "sales", money: true }, { label: "Gross profit", key: "gross_profit", money: true }, { label: "Gross margin %", key: "gross_margin_pct" }, { label: "Below-average margin", key: "below_average_margin" }]} /></State></Card>}
      {section === "discounts" && <Card t="Sales by Discount Level"><State s={discountRows}><ReportTable rows={discountRows.data!} columns={[{ label: "Discount %", key: "discount_pct" }, { label: "Invoice lines", key: "invoice_lines" }, { label: "Units sold", key: "units_sold" }, { label: "Sales", key: "sales", money: true }, { label: "Gross profit", key: "gross_profit", money: true }]} /></State></Card>}
      {section === "dealers" && <Card t="Dealer Performance"><State s={dealerRows}><ReportTable rows={dealerRows.data!} columns={[{ label: "Dealer", key: "dealer_name" }, { label: "Type", key: "customer_type" }, { label: "City", key: "city" }, { label: "State", key: "state" }, { label: "Region", key: "region" }, { label: "Invoices", key: "invoices" }, { label: "Units", key: "units_sold" }, { label: "Sales", key: "sales", money: true }, { label: "Gross profit", key: "gross_profit", money: true }]} /></State></Card>}
      {section === "invoices" && <Card t="Recent Invoices"><State s={invoiceRows}><ReportTable rows={invoiceRows.data!} columns={[{ label: "Invoice", key: "invoice_id" }, { label: "Date", key: "invoice_date" }, { label: "Dealer", key: "dealer_name" }, { label: "City", key: "city" }, { label: "Region", key: "region" }, { label: "Status", key: "status" }, { label: "Line items", key: "line_items" }, { label: "Units", key: "units" }, { label: "Sales", key: "sales", money: true }, { label: "Gross profit", key: "gross_profit", money: true }]} /></State></Card>}
    </main></div>;
}
