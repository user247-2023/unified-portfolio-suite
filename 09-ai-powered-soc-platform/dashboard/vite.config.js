// Vite config for the SOC dashboard.
// Purpose: enable React fast-refresh and a dev server on a fixed port.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
