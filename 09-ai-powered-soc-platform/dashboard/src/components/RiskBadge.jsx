/**
 * RiskBadge component.
 * Purpose: Render an incident's priority + risk score with a severity color.
 * Kept presentational and dependency-free so it's easy to test/restyle.
 */
import React from "react";

const COLORS = {
  P1: "#b91c1c", // red
  P2: "#c2410c", // orange
  P3: "#a16207", // amber
  P4: "#374151", // slate
};

export default function RiskBadge({ priority, score }) {
  const color = COLORS[priority] ?? COLORS.P4;
  return (
    <span
      style={{
        background: color,
        color: "white",
        padding: "2px 8px",
        borderRadius: 6,
        fontVariantNumeric: "tabular-nums",
        fontSize: 12,
      }}
    >
      {priority} · {score}/100
    </span>
  );
}
