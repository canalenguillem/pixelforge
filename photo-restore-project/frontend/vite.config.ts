import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // El dev server está detrás de un reverse proxy externo (red doméstica) que
    // sirve la app en un subdominio. Vite 6 bloquea Hosts no permitidos por
    // seguridad; `true` desactiva esa comprobación (el proxy es de confianza).
    // Alternativa más estricta: allowedHosts: ['fotos.tudominio.com'].
    allowedHosts: true,
    // Necesario para hot-reload dentro de contenedores Docker
    watch: {
      usePolling: true,
    },
    // El navegador llama a /api (mismo origen = subdominio) y el dev server lo
    // reenvía al backend por la red interna de Docker. Así el backend NO necesita
    // puerto expuesto en el host.
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        ws: true, // proxya también el WebSocket de progreso (/jobs/{id}/stream)
      },
    },
    // HMR a través del proxy en un subdominio con HTTPS. Descomentar y ajustar
    // si el hot-reload no conecta desde el navegador:
    // hmr: {
    //   host: 'fotos.tudominio.com',
    //   protocol: 'wss',
    //   clientPort: 443,
    // },
  },
})
