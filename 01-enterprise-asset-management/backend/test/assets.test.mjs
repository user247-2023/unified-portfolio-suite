/**
 * Tests for the asset lifecycle domain.
 * Runnable with the built-in Node test runner (no dependencies):
 *     node --test
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  AssetRegistry,
  AuthorizationError,
  TransitionError,
  NotFoundError,
  canTransition,
} from "../src/domain/assets.mjs";

const admin = { id: "u_admin", roles: ["admin"] };
const auditor = { id: "u_auditor", roles: ["auditor"] };

test("state machine allows and forbids the right transitions", () => {
  assert.ok(canTransition("active", "assigned"));
  assert.ok(canTransition("maintenance", "retired"));
  assert.ok(!canTransition("retired", "active")); // terminal
  assert.ok(!canTransition("active", "bogus"));
});

test("create requires the admin role (default-deny)", () => {
  const reg = new AssetRegistry();
  assert.throws(() => reg.create(auditor, { name: "Laptop", category: "hardware" }),
    AuthorizationError);
  const asset = reg.create(admin, { name: "Laptop", category: "hardware" });
  assert.equal(asset.status, "active");
});

test("assign / retire follow the lifecycle and clear assignment on retire", () => {
  const reg = new AssetRegistry();
  const { id } = reg.create(admin, { name: "Phone", category: "hardware" });
  const assigned = reg.assign(admin, id, "alice");
  assert.equal(assigned.status, "assigned");
  assert.equal(assigned.assignedTo, "alice");

  const retired = reg.retire(admin, id);
  assert.equal(retired.status, "retired");
  assert.equal(retired.assignedTo, null);
});

test("illegal transition throws (retired is terminal)", () => {
  const reg = new AssetRegistry();
  const { id } = reg.create(admin, { name: "Server", category: "hardware" });
  reg.retire(admin, id);
  assert.throws(() => reg.assign(admin, id, "bob"), TransitionError);
});

test("operating on a missing asset throws NotFoundError", () => {
  const reg = new AssetRegistry();
  assert.throws(() => reg.retire(admin, "asset_999"), NotFoundError);
});

test("audit log is append-only and records every mutation", () => {
  const reg = new AssetRegistry();
  const { id } = reg.create(admin, { name: "Monitor", category: "hardware" });
  reg.assign(admin, id, "carol");
  reg.retire(admin, id);

  const trail = reg.audit(id);
  assert.deepEqual(trail.map((e) => e.action), ["create", "assign", "retire"]);

  // Append-only: returned copies can't mutate internal state.
  trail.pop();
  assert.equal(reg.audit(id).length, 3);

  // Records are frozen.
  assert.throws(() => { reg.audit(id)[0].action = "tamper"; }, TypeError);
});
