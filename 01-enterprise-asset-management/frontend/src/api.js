/**
 * Backends for the asset console.
 *
 * The UI talks to a small async interface — list / audit / create / assign /
 * maintenance / retire / setRole — and doesn't care whether it's backed by the
 * real API or the in-memory demo store. `chooseBackend()` probes the API on
 * startup and picks `ApiBackend` if it's reachable, otherwise falls back to the
 * `DemoBackend` so the app always works.
 *
 * Auth note: in local dev the API hands out a short-lived role token via
 * /auth/dev-token. A production build would replace that with real SSO/login;
 * the rest of this client wouldn't change.
 */
import { AssetStore } from "./store.js";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:4000";

export class ApiBackend {
  mode = "live";

  constructor(baseUrl = API_URL) {
    this.baseUrl = baseUrl;
    this.token = null;
    this.role = "admin";
  }

  async setRole(role) {
    const res = await fetch(`${this.baseUrl}/auth/dev-token`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ role }),
    });
    if (!res.ok) throw new Error("Could not obtain a session token.");
    const data = await res.json();
    this.token = data.token;
    this.role = data.role;
    return data.role;
  }

  async #req(path, opts = {}) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...opts,
      headers: {
        "content-type": "application/json",
        Authorization: `Bearer ${this.token}`,
        ...(opts.headers || {}),
      },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Request failed (${res.status}).`);
    }
    return res.json();
  }

  async list() { return (await this.#req("/assets")).assets; }
  async audit() { return (await this.#req("/audit")).audit; }
  create(input) { return this.#req("/assets", { method: "POST", body: JSON.stringify(input) }); }
  assign(id, user) { return this.#req(`/assets/${id}/assign`, { method: "POST", body: JSON.stringify({ user }) }); }
  maintenance(id) { return this.#req(`/assets/${id}/maintenance`, { method: "POST" }); }
  retire(id) { return this.#req(`/assets/${id}/retire`, { method: "POST" }); }
}

/** In-memory backend mirroring the API surface, for offline/demo use. */
export class DemoBackend {
  mode = "demo";

  constructor() {
    this.store = new AssetStore();
    this.role = "admin";
  }

  async setRole(role) { this.role = role; return role; }
  #actor() { return { id: `u_${this.role}`, roles: [this.role] }; }

  async list() { return this.store.list(); }
  async audit() { return this.store.audit(); }
  async create(input) { return this.store.create(this.#actor(), input); }
  async assign(id, user) { return this.store.assign(this.#actor(), id, user); }
  async maintenance(id) { return this.store.sendToMaintenance(this.#actor(), id); }
  async retire(id) { return this.store.retire(this.#actor(), id); }
}

async function apiReachable(baseUrl = API_URL, timeoutMs = 2000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}/health`, { signal: controller.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/** Pick the live backend if the API answers, else the demo store. */
export async function chooseBackend() {
  if (await apiReachable()) {
    const backend = new ApiBackend();
    try {
      await backend.setRole("admin"); // get an initial token
      return backend;
    } catch {
      /* fall through to demo */
    }
  }
  return new DemoBackend();
}
