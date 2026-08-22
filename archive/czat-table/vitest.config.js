import { defineConfig } from "vitest/config"
import path from "node:path"

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    // Most tests are pure (CSV string parsing). The parseCsvFile tests
    // need a DOM — they pin a per-file environment in the test itself.
    environment: "node",
  },
})
