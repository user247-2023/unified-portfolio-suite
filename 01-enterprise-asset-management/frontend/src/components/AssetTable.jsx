/**
 * AssetTable component.
 * Purpose: List assets with their lifecycle status and the valid next actions.
 * Action buttons are shown only for legal transitions (per the state machine)
 * and are disabled when the actor lacks edit rights — the UI never offers an
 * action the domain would reject.
 */
import React from "react";
import StatusBadge from "./StatusBadge.jsx";
import { canTransition } from "../store.js";

export default function AssetTable({ assets, canEdit, onAction }) {
  if (!assets.length) {
    return <p className="empty">No assets yet.</p>;
  }
  return (
    <table className="asset-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Category</th>
          <th>Status</th>
          <th>Assigned to</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {assets.map((a) => (
          <tr key={a.id}>
            <td>{a.name}</td>
            <td className="muted">{a.category}</td>
            <td><StatusBadge status={a.status} /></td>
            <td className="muted">{a.assignedTo || "—"}</td>
            <td className="actions">
              {canTransition(a.status, "assigned") && (
                <button disabled={!canEdit}
                        onClick={() => onAction("assign", a)}>Assign</button>
              )}
              {canTransition(a.status, "maintenance") && (
                <button disabled={!canEdit}
                        onClick={() => onAction("maintenance", a)}>Maintenance</button>
              )}
              {canTransition(a.status, "retired") && (
                <button className="danger" disabled={!canEdit}
                        onClick={() => onAction("retire", a)}>Retire</button>
              )}
              {a.status === "retired" && <span className="muted">terminal</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
