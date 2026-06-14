/**
 * SIEM dashboard root.
 *
 * Purpose: Top-level view that polls the ingestion service for triaged
 * incidents and renders the prioritized queue. Structure only — styling is
 * intentionally minimal so the data flow is clear.
 *
 * Trade-off: short-interval polling keeps the demo simple; a production build
 * would use Server-Sent Events / WebSockets for push and pause polling when the
 * tab is hidden.
 */
import React, { useEffect, useState } from "react";
import { fetchIncidents } from "./api.js";
import IncidentList from "./components/IncidentList.jsx";

const POLL_MS = 5000;

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await fetchIncidents();
        if (active) {
          setIncidents(data.incidents ?? []);
          setError(null);
        }
      } catch (e) {
        if (active) setError(e.message);
      }
    }
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: 24,
                   fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 22 }}>AI-Powered SOC — Incident Queue</h1>
      <p style={{ color: "#6b7280" }}>
        Auto-triaged incidents, most urgent first. Refreshes every{" "}
        {POLL_MS / 1000}s.
      </p>
      {error && (
        <p style={{ color: "#b91c1c" }}>
          Could not reach the ingestion API: {error}
        </p>
      )}
      <IncidentList incidents={incidents} />
    </main>
  );
}
