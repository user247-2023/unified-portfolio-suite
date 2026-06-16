/**
 * AuditLog component.
 * Purpose: Render the append-only audit trail (newest first). Visualizes the
 * compliance property that every mutation is recorded and immutable.
 */
import React from "react";

export default function AuditLog({ entries }) {
  if (!entries.length) {
    return <p className="empty">No audit entries yet.</p>;
  }
  return (
    <ol className="audit-log">
      {entries.map((e) => (
        <li key={e.seq}>
          <span className="audit-action">{e.action}</span>
          <span className="muted"> {e.assetId} by {e.actor}</span>
          {e.details && Object.keys(e.details).length > 0 && (
            <span className="muted"> · {JSON.stringify(e.details)}</span>
          )}
          <time className="muted"> · {new Date(e.ts).toLocaleTimeString()}</time>
        </li>
      ))}
    </ol>
  );
}
