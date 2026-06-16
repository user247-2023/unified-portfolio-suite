// Vite config for the EAMS frontend.
// Purpose: React fast-refresh + a dev server on a fixed port.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
});
