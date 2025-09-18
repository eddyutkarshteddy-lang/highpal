import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: false, // Set to true for HTTPS if needed
    host: true,
    port: 5173
  }
})
