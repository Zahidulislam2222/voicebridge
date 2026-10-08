import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { developmentSettings } from '../../tools/development-settings.mjs';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../../', 'VITE_');
  const settings = developmentSettings(env);
  const { coreProxy, ...server } = settings;
  return {
    plugins: [react()],
    envDir: '../../',
    server: {
      ...server,
      strictPort: true,
      proxy: coreProxy
        ? {
            '/engine-api': {
              target: coreProxy,
              rewrite: (path) => path.replace(/^\/engine-api/, ''),
            },
            '/auth': { target: coreProxy },
          }
        : undefined,
    },
    preview: { ...server, strictPort: true },
  };
});
