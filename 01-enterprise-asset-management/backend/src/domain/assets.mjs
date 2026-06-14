/**
 * Asset lifecycle domain (dependency-free).
 *
 * Purpose: The canonical business rules for the asset registry — the lifecycle
 * state machine, role-based authorization, and the append-only audit trail —
 * with no framework or database dependency. This is the source of truth the
 * Fastify route layer (modules/assets.ts) wraps; keeping it pure makes it
 * runnable and testable with `node --test` (no install needed).
 *
 * Security trade-offs:
 *  - Every mutation requires the "admin" role (default-deny) and is recorded in
 *    an append-only audit log (records are frozen and never removed/mutated),
 *    preserving chain of custody for compliance.
 *  - "retire" is a terminal state, not a delete — history is preserved.
 *  - Illegal lifecycle transitions throw rather than silently no-op.
 */

/** @typedef {"active"|"assigned"|"maintenance"|"retired"} AssetStatus */

export const STATES = ["active", "assigned", "maintenance", "retired"];

// Allowed lifecycle transitions. "retired" is terminal (empty list).
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
export class NotFoundError extends Error {}

function requireRole(actor, role) {
  const roles = (actor && actor.roles) || [];
  if (!roles.includes(role)) {
    throw new AuthorizationError(`action requires role: ${role}`);
  }
}

export class AssetRegistry {
  #assets = new Map();
  #audit = []; // append-only
  #auditSeq = 0;
  #idCounter = 0;

  #log(action, actor, assetId, details) {
    // Append-only: push a frozen record; never mutate or remove entries.
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

  create(actor, { name, category }) {
    requireRole(actor, "admin");
    if (!name || !category) {
      throw new Error("name and category are required");
    }
    const id = `asset_${++this.#idCounter}`;
    const asset = { id, name, category, status: "active", assignedTo: null };
    this.#assets.set(id, asset);
    this.#log("create", actor, id, { name, category });
    return { ...asset };
  }

  #transition(actor, id, to, mutate, action, details) {
    requireRole(actor, "admin");
    const asset = this.#assets.get(id);
    if (!asset) throw new NotFoundError(`asset not found: ${id}`);
    if (!canTransition(asset.status, to)) {
      throw new TransitionError(`illegal transition ${asset.status} -> ${to}`);
    }
    mutate(asset);
    asset.status = to;
    this.#log(action, actor, id, details);
    return { ...asset };
  }

  assign(actor, id, user) {
    if (!user) throw new Error("assign requires a user");
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

  get(id) {
    const a = this.#assets.get(id);
    return a ? { ...a } : null;
  }

  list() {
    return [...this.#assets.values()].map((a) => ({ ...a }));
  }

  /** Audit entries, optionally filtered to one asset. Returns copies. */
  audit(id = null) {
    return this.#audit.filter((e) => id === null || e.assetId === id);
  }
}
