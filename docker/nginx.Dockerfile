FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_WS_PATH
ARG VITE_WS_RECONNECT_BASE_DELAY
ARG VITE_WS_RECONNECT_MAX_DELAY
ENV VITE_WS_PATH=${VITE_WS_PATH}
ENV VITE_WS_RECONNECT_BASE_DELAY=${VITE_WS_RECONNECT_BASE_DELAY}
ENV VITE_WS_RECONNECT_MAX_DELAY=${VITE_WS_RECONNECT_MAX_DELAY}
RUN npm run build

FROM nginx:alpine
ARG NGINX_CONFIG=docker/nginx/default.conf
RUN apk add --no-cache gettext \
    && mkdir -p /etc/nginx/templates
COPY ${NGINX_CONFIG} /etc/nginx/templates/default.conf.template
COPY docker/nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
