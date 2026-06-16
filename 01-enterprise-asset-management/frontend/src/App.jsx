/**
 * EAMS frontend root.
 *
 * Register assets, drive their lifecycle, and switch between an admin and an
 * auditor role to see RBAC in action. On startup it probes the API: if the
 * backend is up it talks to it live (with a dev session token); otherwise it
 * falls back to an in-memory store that mirrors the same rules, so the app runs
 * standalone. The status badge shows which mode you're in. Errors raised by
 * either backend (authorization, illegal transition) surface the same way.
 */
import React, { useEffect, useState } from "react";
import { chooseBackend } from "./api.js";
import AssetTable from "./components/AssetTable.jsx";
import CreateAssetForm from "./components/CreateAssetForm.jsx";
import AuditLog from "./components/AuditLog.jsx";

export default function App() {
  const [backend, setBackend] = useState(null);
  const [mode, setMode] = useState("connecting");
  const [role, setRole] = useState("admin");
  const [assets, setAssets] = useState([]);
  const [audit, setAudit] = useState([]);
  const [message, setMessage] = useState(null);

  const canEdit = role === "admin";

  // Pick a backend (live API or demo store) once on startup.
  useEffect(() => {
    let active = true;
    chooseBackend().then(async (b) => {
      if (!active) return;
      setBackend(b);
      setMode(b.mode);
      await reload(b);
    });
    return () => { active = false; };
  }, []);

  async function reload(b = backend) {
    if (!b) return;
    setAssets(await b.list());
    setAudit(await b.audit());
  }

  async function run(fn, okText) {
    try {
      await fn();
      setMessage(okText ? { type: "ok", text: okText } : null);
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      await reload();
    }
  }

  async function changeRole(next) {
    setRole(next);
    if (backend) {
      await backend.setRole(next);
      await reload();
    }
  }

  function handleCreate(input) {
    run(() => backend.create(input), `Created ${input.name}.`);
  }

  function handleAction(action, asset) {
    if (action === "assign") {
      const user = window.prompt(`Assign "${asset.name}" to which user?`, "bob@corp");
      if (user === null) return;
      run(() => backend.assign(asset.id, user));
    } else if (action === "maintenance") {
      run(() => backend.maintenance(asset.id));
    } else if (action === "retire") {
      run(() => backend.retire(asset.id));
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Enterprise Asset Management</h1>
          <p className="subtitle">Track assets across their lifecycle</p>
        </div>
        <div className="header-right">
          <span className={`source-badge source-${mode}`}>
            {mode === "live" && "● live API"}
            {mode === "demo" && "● demo (in-memory)"}
            {mode === "connecting" && "○ connecting…"}
          </span>
          <label className="role-switch">
            Acting as:
            <select value={role} onChange={(e) => changeRole(e.target.value)}>
              <option value="admin">Admin</option>
              <option value="auditor">Auditor (read-only)</option>
            </select>
          </label>
        </div>
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
