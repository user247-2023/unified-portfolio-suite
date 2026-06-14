/**
 * IncidentList component.
 * Purpose: Render the triaged incident queue (most urgent first) with each
 * incident's entities, triggered rules, risk rationale, and recommended actions.
 * This is the analyst's primary working surface.
 */
import React from "react";
import RiskBadge from "./RiskBadge.jsx";

export default function IncidentList({ incidents }) {
  if (!incidents?.length) {
    return <p style={{ color: "#6b7280" }}>No open incidents. 🎉</p>;
  }
  return (
    <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 12 }}>
      {incidents.map((inc) => (
        <li
          key={inc.id}
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            padding: 16,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>{inc.alert_rules.join(", ")}</strong>
            <RiskBadge priority={inc.priority} score={inc.risk_score} />
          </div>
          <div style={{ color: "#6b7280", fontSize: 13, marginTop: 4 }}>
            Entities: {inc.entities.join(", ")}
          </div>

          <details style={{ marginTop: 8 }}>
            <summary style={{ cursor: "pointer" }}>Why this score</summary>
            <ul>
              {inc.rationale.map((line, i) => (
                <li key={i} style={{ fontSize: 13 }}>{line}</li>
              ))}
            </ul>
          </details>

          <div style={{ marginTop: 8 }}>
            <strong style={{ fontSize: 13 }}>Recommended actions</strong>
            <ol>
              {inc.recommended_actions.map((a, i) => (
                <li key={i} style={{ fontSize: 13 }}>{a}</li>
              ))}
            </ol>
          </div>
        </li>
      ))}
    </ul>
  );
}
