/**
 * SIEM dashboard API client.
 *
 * Purpose: Thin wrapper over the ingestion service's read endpoints.
 *
 * Security notes:
 *  - The API base URL and key come from build-time env (VITE_API_URL,
 *    VITE_API_KEY) — never hardcoded. In a real deployment the dashboard would
 *    authenticate the USER (SSO/session) and proxy to the API server-side
 *    rather than shipping an API key to the browser; this client documents that
 *    boundary.
 */
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

async function request(path) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: API_KEY ? { "X-API-Key": API_KEY } : {},
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function fetchIncidents() {
  return request("/incidents");
}

export function fetchHealth() {
  return request("/healthz");
}
