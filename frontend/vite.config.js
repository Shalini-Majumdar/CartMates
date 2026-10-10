import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // listen on all interfaces so the container is reachable
    // File-change events do not cross a Windows bind mount into the container,
    // so docker-compose sets VITE_USE_POLLING to have Vite poll for edits.
    watch: { usePolling: process.env.VITE_USE_POLLING === "true" },
  },
  build: {
    outDir: "build",
  },
});
