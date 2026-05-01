FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache openssl
RUN mkdir -p /etc/nginx/certs && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout /etc/nginx/certs/server.key \
      -out /etc/nginx/certs/server.crt \
      -subj "/C=CH/ST=Vaud/L=Lausanne/O=42/CN=localhost"
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80 443
