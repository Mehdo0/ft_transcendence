#!/bin/sh
set -eu

if [ "${TLS_ENABLED:-false}" = "true" ]; then
  mkdir -p /etc/nginx/certs
  cp /run/secrets/server_crt /etc/nginx/certs/server.crt
  cp /run/secrets/server_key /etc/nginx/certs/server.key
fi

envsubst '${DOMAIN}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec "$@"
