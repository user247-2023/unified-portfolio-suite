/**
 * SummaryBar component.
 * Purpose: At-a-glance incident counts by priority + the highest current risk
 * score — the top-of-fold situational awareness a SOC analyst wants first.
 */
import React from "react";

const PRIORITIES = ["P1", "P2", "P3", "P4"];

export default function SummaryBar({ incidents }) {
  const counts = PRIORITIES.reduce((acc, p) => {
    acc[p] = incidents.filter((i) => i.priority === p).length;
    return acc;
  }, {});
  const maxRisk = incidents.reduce((m, i) => Math.max(m, i.risk_score ?? 0), 0);

  return (
    <div className="summary-bar">
      {PRIORITIES.map((p) => (
        <div key={p} className={`stat stat-${p.toLowerCase()}`}>
          <span className="stat-value">{counts[p]}</span>
          <span className="stat-label">{p}</span>
        </div>
      ))}
      <div className="stat stat-total">
        <span className="stat-value">{incidents.length}</span>
        <span className="stat-label">open</span>
      </div>
      <div className="stat stat-risk">
        <span className="stat-value">{maxRisk}</span>
        <span className="stat-label">max risk</span>
      </div>
    </div>
  );
}
