/**
 * RiskBadge component.
 * Purpose: Render an incident's priority + risk score with a priority color.
 * Presentational and class-driven (see index.css) so the palette lives in one place.
 */
import React from "react";

export default function RiskBadge({ priority, score }) {
  const cls = `badge badge-${(priority || "p4").toLowerCase()}`;
  return (
    <span className={cls}>
      {priority} · {score}/100
    </span>
  );
}
