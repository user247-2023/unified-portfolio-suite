/**
 * EAMS frontend root.
 *
 * Purpose: The asset-management console — register assets, drive their
 * lifecycle, switch between an admin and an auditor role to demonstrate RBAC,
 * and watch the append-only audit trail update in real time.
 *
 * Demo mode: state lives in an in-memory store that mirrors the backend domain
 * (same state machine, RBAC, audit rules), so the app runs standalone. Errors
 * raised by the domain (authorization, illegal transition) are surfaced to the
 * user exactly as the API would.
 */
import React, { useMemo, useRef, useState } from "react";
import { AssetStore } from "./store.js";
import AssetTable from "./components/AssetTable.jsx";
import CreateAssetForm from "./components/CreateAssetForm.jsx";
import AuditLog from "./components/AuditLog.jsx";

const ROLES = {
  admin: { id: "u_admin", roles: ["admin"], label: "Admin" },
  auditor: { id: "u_auditor", roles: ["auditor"], label: "Auditor (read-only)" },
};

export default function App() {
  const storeRef = useRef(null);
  if (storeRef.current === null) storeRef.current = new AssetStore();
  const store = storeRef.current;

  const [roleKey, setRoleKey] = useState("admin");
  const [tick, setTick] = useState(0); // bump to re-read the store
  const [message, setMessage] = useState(null);

  const actor = ROLES[roleKey];
  const canEdit = actor.roles.includes("admin");

  const assets = useMemo(() => store.list(), [store, tick]);
  const audit = useMemo(() => store.audit(), [store, tick]);

  function refresh() {
    setTick((t) => t + 1);
  }

  function run(fn) {
    try {
      fn();
      setMessage(null);
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      refresh();
    }
  }

  function handleCreate(input) {
    run(() => {
      const a = store.create(actor, input);
      setMessage({ type: "ok", text: `Created ${a.name}.` });
    });
  }

  function handleAction(action, asset) {
    if (action === "assign") {
      const user = window.prompt(`Assign "${asset.name}" to which user?`, "bob@corp");
      if (user === null) return;
      run(() => store.assign(actor, asset.id, user));
    } else if (action === "maintenance") {
      run(() => store.sendToMaintenance(actor, asset.id));
    } else if (action === "retire") {
      run(() => store.retire(actor, asset.id));
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Enterprise Asset Management</h1>
          <p className="subtitle">Track assets across their lifecycle · demo (in-memory) mode</p>
        </div>
        <label className="role-switch">
          Acting as:
          <select value={roleKey} onChange={(e) => setRoleKey(e.target.value)}>
            {Object.entries(ROLES).map(([k, r]) => (
              <option key={k} value={k}>{r.label}</option>
            ))}
          </select>
        </label>
      </header>

      {message && (
        <div className={`message message-${message.type}`}>{message.text}</div>
      )}

      <section className="panel">
        <h2>Register asset</h2>
        <CreateAssetForm canEdit={canEdit} onCreate={handleCreate} />
      </section>

      <section className="panel">
        <h2>Assets <span className="count">{assets.length}</span></h2>
        <AssetTable assets={assets} canEdit={canEdit} onAction={handleAction} />
      </section>

      <section className="panel">
        <h2>Audit trail <span className="count">{audit.length}</span>
          <span className="hint"> (append-only)</span></h2>
        <AuditLog entries={audit} />
      </section>
    </div>
  );
}
