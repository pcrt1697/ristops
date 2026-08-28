# syntax=docker/dockerfile:1

# Prod-like frontend: static assets built by Vite, served by nginx.
# Local development still uses `npm run dev` on the host.

FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* vars at build time, so these are build args rather than
# runtime env. Both must be reachable from the *browser*, never compose DNS names.
ARG VITE_RISTOPS_BFF_URL
ARG VITE_RISTOPS_OTEL_URL
ENV VITE_RISTOPS_BFF_URL=${VITE_RISTOPS_BFF_URL} \
    VITE_RISTOPS_OTEL_URL=${VITE_RISTOPS_OTEL_URL}

RUN npm run build


FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
