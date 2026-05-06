#!/bin/sh
set -e
mkdir -p /etc/nginx/certs
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /etc/nginx/certs/server.key \
  -out /etc/nginx/certs/server.crt \
  -subj "/C=CH/ST=Vaud/L=Lausanne/O=42/CN=localhost"
exec nginx -g 'daemon off;'
