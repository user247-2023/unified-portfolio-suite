/**
 * Client-side asset store (demo / offline mode).
 *
 * Purpose: A faithful browser port of the backend lifecycle domain
 * (backend/src/domain/assets.mjs): the same state machine, role-based
 * authorization (default-deny), and append-only audit trail. This lets the UI
 * run and be demoed WITHOUT the Fastify API; in a real deployment these calls
 * would hit the REST API instead, but the rules — and the failures they raise —
 * are intentionally identical so the UX matches.
 *
 * Security note: the client enforcing RBAC is for UX only; the server is always
 * the real authority. We mirror the rules here so the demo behaves correctly.
 */
export const STATES = ["active", "assigned", "maintenance", "retired"];

const TRANSITIONS = {
  active: ["assigned", "maintenance", "retired"],
  assigned: ["active", "maintenance", "retired"],
  maintenance: ["active", "assigned", "retired"],
  retired: [],
};

export function canTransition(from, to) {
  const allowed = TRANSITIONS[from];
  return allowed ? allowed.includes(to) : false;
}

export class AuthorizationError extends Error {}
export class TransitionError extends Error {}

function requireRole(actor, role) {
  const roles = (actor && actor.roles) || [];
  if (!roles.includes(role)) {
    throw new AuthorizationError(`This action requires the "${role}" role.`);
  }
}

export class AssetStore {
  #assets = new Map();
  #audit = [];
  #auditSeq = 0;
  #idCounter = 0;

  constructor(seed = true) {
    if (seed) this.#seed();
  }

  #log(action, actor, assetId, details) {
    this.#audit.push(
      Object.freeze({
        seq: ++this.#auditSeq,
        ts: Date.now(),
        action,
        actor: (actor && actor.id) || "unknown",
        assetId,
        details: Object.freeze({ ...details }),
      }),
    );
  }

  #seed() {
    const sys = { id: "system", roles: ["admin"] };
    const a = this.create(sys, { name: 'MacBook Pro 16"', category: "hardware" });
    this.assign(sys, a.id, "alice@corp");
    this.create(sys, { name: "Adobe CC license", category: "license" });
    const c = this.create(sys, { name: "Dell PowerEdge R750", category: "hardware" });
    this.sendToMaintenance(sys, c.id);
  }

  create(actor, { name, category }) {
    requireRole(actor, "admin");
    if (!name || !category) throw new Error("Name and category are required.");
    const id = `asset_${++this.#idCounter}`;
    const asset = { id, name, category, status: "active", assignedTo: null };
    this.#assets.set(id, asset);
    this.#log("create", actor, id, { name, category });
    return { ...asset };
  }

  #transition(actor, id, to, mutate, action, details) {
    requireRole(actor, "admin");
    const asset = this.#assets.get(id);
    if (!asset) throw new Error(`Asset not found: ${id}`);
    if (!canTransition(asset.status, to)) {
      throw new TransitionError(`Cannot move ${asset.status} → ${to}.`);
    }
    mutate(asset);
    asset.status = to;
    this.#log(action, actor, id, details);
    return { ...asset };
  }

  assign(actor, id, user) {
    if (!user) throw new Error("Assignment requires a user.");
    return this.#transition(actor, id, "assigned",
      (a) => { a.assignedTo = user; }, "assign", { user });
  }

  sendToMaintenance(actor, id) {
    return this.#transition(actor, id, "maintenance",
      (a) => { a.assignedTo = null; }, "maintenance", {});
  }

  retire(actor, id) {
    return this.#transition(actor, id, "retired",
      (a) => { a.assignedTo = null; }, "retire", {});
  }

  list() {
    return [...this.#assets.values()].map((a) => ({ ...a }));
  }

  audit() {
    return [...this.#audit].reverse(); // newest first
  }
}
