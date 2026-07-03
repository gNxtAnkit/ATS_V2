import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev port pinned to 5173 to match PLATFORM_ADMIN_APP_BASE_URL / the
// FRONTEND_PLATFORM_ADMIN_* email links configured in the root .env, and to
// avoid colliding with web-tenant (5173).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  preview: {
    port: 5173,
    strictPort: true,
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
