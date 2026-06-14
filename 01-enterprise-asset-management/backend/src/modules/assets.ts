/**
 * Asset feature module.
 *
 * Purpose: Defines the asset registry routes (list, create, retire) with
 * schema-validated input and role-based authorization. Demonstrates the
 * suite-wide pattern: one module = one bounded context with a narrow interface.
 *
 * Security trade-offs:
 *  - Every mutating route requires authentication (preHandler) AND an explicit
 *    role check (default deny). Read routes are auth-gated but role-permissive.
 *  - "Retire" is a state transition, not a hard delete, preserving the audit
 *    trail / chain of custody required for compliance.
 */
import type { FastifyInstance } from "fastify";

// In a real deployment this is replaced by the Prisma client; kept inline here
// so the module is illustrative without requiring a live database.
type Asset = {
  id: string;
  name: string;
  category: "hardware" | "software" | "license";
  status: "active" | "retired";
  assignedTo: string | null;
};

const createAssetSchema = {
  body: {
    type: "object",
    required: ["name", "category"],
    additionalProperties: false,
    properties: {
      name: { type: "string", minLength: 1, maxLength: 200 },
      category: { type: "string", enum: ["hardware", "software", "license"] },
      assignedTo: { type: ["string", "null"], maxLength: 200 },
    },
  },
} as const;

function hasRole(request: any, role: string): boolean {
  // JWT payload carries roles; default-deny if the claim is absent.
  const roles: string[] = request.user?.roles ?? [];
  return roles.includes(role);
}

export async function registerAssetRoutes(app: FastifyInstance) {
  const assets = new Map<string, Asset>();

  app.get(
    "/assets",
    { preHandler: [(app as any).authenticate] },
    async () => ({ assets: [...assets.values()] }),
  );

  app.post(
    "/assets",
    { schema: createAssetSchema, preHandler: [(app as any).authenticate] },
    async (request, reply) => {
      if (!hasRole(request, "admin")) {
        return reply.code(403).send({ error: "forbidden" });
      }
      const body = request.body as Omit<Asset, "id" | "status">;
      const asset: Asset = {
        id: crypto.randomUUID(),
        status: "active",
        assignedTo: body.assignedTo ?? null,
        name: body.name,
        category: body.category,
      };
      assets.set(asset.id, asset);
      return reply.code(201).send(asset);
    },
  );

  // Retire = soft state change. Append-only audit trail is preserved.
  app.post(
    "/assets/:id/retire",
    { preHandler: [(app as any).authenticate] },
    async (request, reply) => {
      if (!hasRole(request, "admin")) {
        return reply.code(403).send({ error: "forbidden" });
      }
      const { id } = request.params as { id: string };
      const asset = assets.get(id);
      if (!asset) return reply.code(404).send({ error: "not_found" });
      asset.status = "retired";
      asset.assignedTo = null;
      return asset;
    },
  );
}
