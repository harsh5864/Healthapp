import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The proxy keeps local React-to-Spring requests same-origin during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
});
