import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  base: './',
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
        // Content-hashed filenames → long-term browser cache re-use.
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('framer-motion')) return 'framer';
          if (id.includes('cmdk')) return 'cmdk';
          if (id.includes('@tanstack')) return 'tanstack';
          if (id.includes('react-dom') || id.includes('react/')) return 'react';
          // Keep lucide-react in main bundle: icons are used everywhere
          // (every drawer, every UI primitive). Splitting it gave us
          // 200KB main + 200KB lucide chunk with worse cache reuse.
        },
      },
    },
    target: 'es2020',
    minify: 'oxc',
    cssMinify: true,
    cssCodeSplit: true, // per-chunk CSS → smaller first paint + better cache reuse
    sourcemap: false,
    chunkSizeWarningLimit: 600,
    reportCompressedSize: false, // skip gzip size logging for faster builds
  },
})
