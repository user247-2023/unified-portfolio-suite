/**
 * Dashboard bootstrap.
 * Purpose: Mount the React SIEM dashboard into the page.
 */
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
