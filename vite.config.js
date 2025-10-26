import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // Force pre-bundling of VAD so its CommonJS build works under ESM/dev server
    include: ['@ricky0123/vad-web', 'onnxruntime-web'],
    esbuildOptions: {
      target: 'esnext'
    }
  },
  worker: {
    format: 'es',
    plugins: () => []
  },
  build: {
    target: 'esnext',
    sourcemap: false, // Disable sourcemap warnings
    rollupOptions: {
      onwarn(warning, warn) {
        // Suppress sourcemap warnings for VAD library
        if (warning.code === 'SOURCEMAP_ERROR' && warning.message.includes('@ricky0123/vad-web')) {
          return;
        }
        warn(warning);
      }
    }
  },
  server: {
    https: false,
    host: true,
    port: 5173,
    hmr: {
      overlay: true
    },
    headers: {
      // Credentialless mode allows SharedArrayBuffer without strict CORP
      'Cross-Origin-Embedder-Policy': 'credentialless',
      'Cross-Origin-Opener-Policy': 'same-origin'
    },
    fs: {
      strict: false
    }
  }
})
