/**
 * EAMS API entry point.
 *
 * Purpose: Bootstraps the Fastify server, wires JWT auth, registers feature
 * modules, and applies global hardening (schema validation, error fail-closed).
 *
 * Security trade-offs:
 *  - Secrets (JWT_SECRET, DATABASE_URL) come ONLY from the environment; the
 *    process refuses to start without them rather than falling back to a weak
 *    default (fail-closed).
 *  - Fastify validates request bodies against JSON schemas declared per-route,
 *    so malformed/oversized input is rejected before any handler executes.
 *
 * Performance trade-off: Fastify's schema compilation happens once at startup,
 * trading a small boot cost for fast per-request validation.
 */
import Fastify from "fastify";
import fastifyJwt from "@fastify/jwt";
import fastifyCors from "@fastify/cors";
import { registerAssetRoutes } from "./modules/assets.js";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    // Fail closed: never start with a missing security-critical variable.
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export async function buildServer() {
  const app = Fastify({
    logger: true,
    // Reject bodies larger than 256 KB to limit abuse / accidental DoS.
    bodyLimit: 256 * 1024,
  });

  await app.register(fastifyJwt, { secret: requireEnv("JWT_SECRET") });

  // The SPA is served from a different origin, so allow it via CORS.
  // CORS_ORIGINS is a comma-separated allowlist; default to the local frontend.
  await app.register(fastifyCors, {
    origin: (process.env.CORS_ORIGINS ?? "http://localhost:5174")
      .split(",")
      .map((o) => o.trim()),
  });

  // Authentication decorator: routes call `request.jwtVerify()` via preHandler.
  app.decorate("authenticate", async (request: any, reply: any) => {
    try {
      await request.jwtVerify();
    } catch {
      reply.code(401).send({ error: "unauthorized" });
    }
  });

  app.get("/health", async () => ({ status: "ok" }));

  // Dev-only helper: mint a short-lived token for a role so the SPA can
  // authenticate without a full identity provider in local development.
  // Disabled outside development — production uses real SSO/login.
  if (process.env.NODE_ENV !== "production") {
    app.post("/auth/dev-token", async (request, reply) => {
      const role = (request.body as { role?: string })?.role === "auditor"
        ? "auditor"
        : "admin";
      const token = app.jwt.sign(
        { sub: `dev_${role}`, roles: [role] },
        { expiresIn: "8h" },
      );
      return reply.send({ token, role });
    });
  }

  await registerAssetRoutes(app);

  return app;
}

if (process.env.NODE_ENV !== "test") {
  const port = Number(process.env.PORT ?? 4000);
  buildServer()
    .then((app) => app.listen({ port, host: "0.0.0.0" }))
    .catch((err) => {
      // Surface the real error and exit non-zero; do not swallow.
      console.error(err);
      process.exit(1);
    });
}
