/**
 * StatusBadge component.
 * Purpose: Color-coded asset lifecycle status pill. Class-driven (see index.css).
 */
import React from "react";

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}
