import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backend = 'http://127.0.0.1:8000';

function apiProxy() {
  return {
    target: backend,
    changeOrigin: true,
    configure(proxy) {
      proxy.on('proxyReq', (request) => request.setHeader('origin', backend));
    },
  };
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': apiProxy(),
      '^/s/[^/]+/(video|report)$': apiProxy(),
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
});
