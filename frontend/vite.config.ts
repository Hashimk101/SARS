import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend (api/index.py) runs on :8000 in development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
