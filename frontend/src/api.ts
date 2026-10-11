export type Filters = { start: string; end: string; region: string; category: string; segment: string };
export const qs = (f: Filters) => new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString();
export async function get<T>(path: string, f: Partial<Filters>, signal: AbortSignal): Promise<T> {
  const r = await fetch(`/api${path}?${qs(f as Filters)}`, { signal });
  if (!r.ok) throw new Error(`${r.status} ${(await r.json().catch(() => ({}))).detail ?? "Request failed"}`);
  return r.json();
}
