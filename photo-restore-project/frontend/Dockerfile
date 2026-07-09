# ==============================================================================
# Photo Restore Pro - Frontend Dockerfile
# ==============================================================================
# Imagen de DESARROLLO (Vite dev server con HMR, usada por docker-compose).
# La configuración multi-stage para PRODUCCIÓN (build + Nginx) está más abajo,
# comentada.
# ==============================================================================

FROM node:20-alpine

WORKDIR /app

# Instalar dependencias primero (mejor cache de capas)
COPY package.json package-lock.json* ./
RUN npm install

# Copiar el resto (en dev el volumen de docker-compose lo sobrescribe)
COPY . .

EXPOSE 5173

# docker-compose sobreescribe con: npm run dev -- --host 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ==============================================================================
# PRODUCCIÓN - Multi-stage build (descomentar y reemplazar el bloque de arriba)
# ==============================================================================
#
# ---- Stage 1: build ---------------------------------------------------------
# FROM node:20-alpine AS build
#
# WORKDIR /app
#
# COPY package.json package-lock.json* ./
# RUN npm ci
#
# COPY . .
# RUN npm run build          # genera /app/dist
#
# ---- Stage 2: serve (Nginx) -------------------------------------------------
# FROM nginx:1.27-alpine AS runtime
#
# # Config de Nginx para SPA (fallback a index.html)
# COPY nginx.spa.conf /etc/nginx/conf.d/default.conf
# COPY --from=build /app/dist /usr/share/nginx/html
#
# EXPOSE 80
#
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#     CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
#
# CMD ["nginx", "-g", "daemon off;"]
# ==============================================================================
