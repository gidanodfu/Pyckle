import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

const backend = process.env.VITE_BACKEND_URL || "http://backend:8000";

export default defineConfig({
  plugins: [tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
      "/ws": { target: backend, ws: true, changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
