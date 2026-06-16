/**
 * SIEM dashboard API client.
 *
 * Purpose: Thin wrapper over the ingestion service's read endpoints, with a
 * graceful demo fallback so the UI is fully renderable without a backend.
 *
 * Security notes:
 *  - The API base URL and key come from build-time env (VITE_API_URL,
 *    VITE_API_KEY) — never hardcoded. In a real deployment the dashboard would
 *    authenticate the USER (SSO/session) and proxy to the API server-side
 *    rather than shipping an API key to the browser; this client documents that
 *    boundary.
 *  - Demo mode is opt-in/automatic for local review only and is clearly flagged
 *    in the UI so demo data is never mistaken for live telemetry.
 */
import { DEMO_INCIDENTS } from "./demo.js";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";
const FORCE_DEMO = import.meta.env.VITE_DEMO === "1";

async function request(path, { timeoutMs = 4000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: API_KEY ? { "X-API-Key": API_KEY } : {},
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Returns { incidents, source } where source is "live" or "demo".
 * Falls back to demo data when the backend is unreachable so the dashboard is
 * always renderable.
 */
export async function fetchIncidents() {
  if (FORCE_DEMO) {
    return { incidents: DEMO_INCIDENTS, source: "demo" };
  }
  try {
    const data = await request("/incidents");
    return { incidents: data.incidents ?? [], source: "live" };
  } catch {
    return { incidents: DEMO_INCIDENTS, source: "demo" };
  }
}
