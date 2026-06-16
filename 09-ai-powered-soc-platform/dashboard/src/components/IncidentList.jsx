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
    return <p className="empty">No open incidents.</p>;
  }
  return (
    <ul className="incident-list">
      {incidents.map((inc) => (
        <li key={inc.id} className={`incident prio-${(inc.priority || "p4").toLowerCase()}`}>
          <div className="incident-top">
            <span className="incident-rules">{inc.alert_rules.join(" · ")}</span>
            <RiskBadge priority={inc.priority} score={inc.risk_score} />
          </div>
          <div className="incident-entities">entities: {inc.entities.join(", ")}</div>

          <details>
            <summary>Why this score</summary>
            <ul>
              {inc.rationale.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </details>

          <div className="actions-title">Recommended actions</div>
          <ol>
            {inc.recommended_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ol>
        </li>
      ))}
    </ul>
  );
}
