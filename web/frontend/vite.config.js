import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // backend FastAPI na :8000 — ten sam origin w dev, bez CORS
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
