import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `allowedHosts` lets the dev server answer requests whose Host header is a
// docker service name (e.g. "frontend-e2e"). Vite 4.5.x's DNS-rebinding guard
// otherwise returns 403 for any non-localhost Host. Extra entries via
// VITE_ALLOWED_HOSTS (comma-separated) for other environments.
const extraHosts = (process.env.VITE_ALLOWED_HOSTS ?? "")
  .split(",")
  .map((h) => h.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: ["localhost", "127.0.0.1", "frontend-e2e", ...extraHosts],
  },
});
