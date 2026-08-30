import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
        // rewrite: don't strip /api — backend serves it as-is
      },
    },
  },
  build: {
    // Split heavy vendor chunks so the initial bundle stays small.
    // AnalyticsView pulls Recharts (~100KB) and lives in its own chunk
    // thanks to React.lazy() in App.jsx; this manual split covers
    // everything else.
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('framer-motion')) return 'framer';
          if (id.includes('cmdk')) return 'cmdk';
          if (id.includes('@tanstack')) return 'tanstack';
          if (id.includes('react-dom') || id.includes('react/')) return 'react';
          if (id.includes('lucide-react')) return 'lucide';
        },
      },
    },
    target: 'es2020',
    minify: 'oxc',
    cssMinify: true,
    sourcemap: false,
    chunkSizeWarningLimit: 600,
  },
})
