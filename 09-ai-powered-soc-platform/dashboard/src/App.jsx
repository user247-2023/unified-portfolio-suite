/**
 * SIEM dashboard root.
 *
 * Purpose: Top-level view that polls the ingestion service for triaged
 * incidents and renders the prioritized queue with summary stats. Falls back to
 * demo data (clearly flagged) when no backend is reachable, so the dashboard is
 * always renderable.
 *
 * Trade-off: short-interval polling keeps the demo simple; a production build
 * would use Server-Sent Events / WebSockets for push and pause polling when the
 * tab is hidden.
 */
import React, { useEffect, useState } from "react";
import { fetchIncidents } from "./api.js";
import SummaryBar from "./components/SummaryBar.jsx";
import IncidentList from "./components/IncidentList.jsx";

const POLL_MS = 5000;

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [source, setSource] = useState("loading");
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      const { incidents: data, source: src } = await fetchIncidents();
      if (!active) return;
      setIncidents(data);
      setSource(src);
      setUpdatedAt(new Date());
    }
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>AI-Powered SOC</h1>
          <p className="subtitle">Automated incident triage queue</p>
        </div>
        <div className={`source-badge source-${source}`}>
          {source === "live" && "● live"}
          {source === "demo" && "● demo data (no backend)"}
          {source === "loading" && "○ connecting…"}
        </div>
      </header>

      <SummaryBar incidents={incidents} />

      <div className="queue-meta">
        <span>{incidents.length} open incident(s), most urgent first</span>
        {updatedAt && (
          <span>updated {updatedAt.toLocaleTimeString()} · refreshes {POLL_MS / 1000}s</span>
        )}
      </div>

      <IncidentList incidents={incidents} />

      <footer className="app-footer">
        Risk scores are explainable (expand “Why this score”). Recommended actions
        are for analyst/SOAR review — triage never auto-remediates.
      </footer>
    </div>
  );
}
