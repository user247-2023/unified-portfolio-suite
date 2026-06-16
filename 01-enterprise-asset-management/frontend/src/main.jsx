/**
 * EAMS frontend bootstrap.
 * Purpose: Mount the asset-management console and load the theme.
 */
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
