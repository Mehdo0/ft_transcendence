FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache openssl
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
