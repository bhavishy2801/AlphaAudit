import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dashboard is fully static: it reads results.json from /public,which the
// Python pipeline mirrors there on every run. No backend required.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: { port: 5173,open: false },
  build: {
    outDir: "dist",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react","react-dom"],
          charts: ["recharts"],
          motion: ["framer-motion"],
        },
      },
    },
  },
});
