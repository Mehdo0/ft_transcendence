#!/bin/sh
set -e
mkdir -p /etc/nginx/certs
cp /run/secrets/server_crt /etc/nginx/certs/server.crt
cp /run/secrets/server_key /etc/nginx/certs/server.key
exec nginx -g 'daemon off;'
