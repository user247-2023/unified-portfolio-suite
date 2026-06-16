// Asset registry routes.
//
// One bounded context: register assets and move them through their lifecycle
// (active → assigned → maintenance → retired). Mutations require the "admin"
// role; reads are open to any authenticated user. "Retire" is a terminal state,
// not a delete, so history is preserved — and every mutation lands in an
// append-only audit log exposed at GET /audit.
//
// The transition rules below mirror the framework-free domain in
// src/domain/assets.mjs (which has its own `node --test` suite); they're kept in
// TS here so the route layer is self-contained and easy to run.
import type { FastifyInstance } from "fastify";

type Status = "active" | "assigned" | "maintenance" | "retired";
type Category = "hardware" | "software" | "license";

interface Asset {
  id: string;
  name: string;
  category: Category;
  status: Status;
  assignedTo: string | null;
}

interface AuditEntry {
  seq: number;
  ts: number;
  action: string;
  actor: string;
  assetId: string;
  details: Record<string, unknown>;
}

const TRANSITIONS: Record<Status, Status[]> = {
  active: ["assigned", "maintenance", "retired"],
  assigned: ["active", "maintenance", "retired"],
  maintenance: ["active", "assigned", "retired"],
  retired: [],
};

const canTransition = (from: Status, to: Status) => TRANSITIONS[from].includes(to);

const createAssetSchema = {
  body: {
    type: "object",
    required: ["name", "category"],
    additionalProperties: false,
    properties: {
      name: { type: "string", minLength: 1, maxLength: 200 },
      category: { type: "string", enum: ["hardware", "software", "license"] },
    },
  },
} as const;

const assignSchema = {
  body: {
    type: "object",
    required: ["user"],
    additionalProperties: false,
    properties: { user: { type: "string", minLength: 1, maxLength: 200 } },
  },
} as const;

const isAdmin = (request: any): boolean =>
  (request.user?.roles ?? []).includes("admin"); // default-deny

export async function registerAssetRoutes(app: FastifyInstance) {
  const assets = new Map<string, Asset>();
  const audit: AuditEntry[] = [];
  let seq = 0;

  const log = (action: string, actor: string, assetId: string, details: Record<string, unknown> = {}) => {
    audit.push({ seq: ++seq, ts: Date.now(), action, actor, assetId, details });
  };

  // Seed data so a freshly-started server (and the wired frontend) has something
  // to show. Recorded in the audit log just like any other mutation.
  const seed = (name: string, category: Category): Asset => {
    const asset: Asset = { id: crypto.randomUUID(), name, category, status: "active", assignedTo: null };
    assets.set(asset.id, asset);
    log("create", "system", asset.id, { name, category });
    return asset;
  };
  const laptop = seed('MacBook Pro 16"', "hardware");
  laptop.status = "assigned";
  laptop.assignedTo = "alice@corp";
  log("assign", "system", laptop.id, { user: "alice@corp" });
  seed("Adobe CC license", "license");

  const auth = (app as any).authenticate;

  app.get("/assets", { preHandler: [auth] }, async () => ({
    assets: [...assets.values()],
  }));

  app.get("/audit", { preHandler: [auth] }, async () => ({
    audit: [...audit].reverse(), // newest first
  }));

  app.post("/assets", { schema: createAssetSchema, preHandler: [auth] }, async (request, reply) => {
    if (!isAdmin(request)) return reply.code(403).send({ error: "forbidden" });
    const { name, category } = request.body as { name: string; category: Category };
    const asset: Asset = { id: crypto.randomUUID(), name, category, status: "active", assignedTo: null };
    assets.set(asset.id, asset);
    log("create", (request as any).user?.sub ?? "unknown", asset.id, { name, category });
    return reply.code(201).send(asset);
  });

  // Generic lifecycle transition handler, reused by the action routes below.
  // `mutate` also gets the request so handlers like "assign" can read the body.
  function transition(action: string, to: Status, mutate: (a: Asset, request: any) => void) {
    return async (request: any, reply: any) => {
      if (!isAdmin(request)) return reply.code(403).send({ error: "forbidden" });
      const asset = assets.get(request.params.id);
      if (!asset) return reply.code(404).send({ error: "not_found" });
      if (!canTransition(asset.status, to)) {
        return reply.code(409).send({ error: `illegal transition ${asset.status} -> ${to}` });
      }
      mutate(asset, request);
      asset.status = to;
      log(action, request.user?.sub ?? "unknown", asset.id, request.body ?? {});
      return asset;
    };
  }

  app.post("/assets/:id/assign", { schema: assignSchema, preHandler: [auth] },
    transition("assign", "assigned", (a, request) => { a.assignedTo = request.body.user; }));
  app.post("/assets/:id/maintenance", { preHandler: [auth] },
    transition("maintenance", "maintenance", (a) => { a.assignedTo = null; }));
  app.post("/assets/:id/retire", { preHandler: [auth] },
    transition("retire", "retired", (a) => { a.assignedTo = null; }));
}
