import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    host: "0.0.0.0",
    port: 5173,

    proxy: {
      "/predict": { target: "http://backend:8000", changeOrigin: true },
      "/health": { target: "http://backend:8000", changeOrigin: true },
      "/tickers": { target: "http://backend:8000", changeOrigin: true },
      "/model": { target: "http://backend:8000", changeOrigin: true },
      "/stock": { target: "http://backend:8000", changeOrigin: true },
      "/plots": { target: "http://backend:8000", changeOrigin: true },
    },
  },
});
