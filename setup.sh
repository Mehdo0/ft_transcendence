#!/usr/bin/env bash
mkdir -p secrets

openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout ./secrets/server.key \
  -out ./secrets/server.crt \
  -subj "/C=CH/ST=Vaud/L=Lausanne/O=42/CN=localhost"

openssl rand -base64 32 | tr '+/' '-_' | tr -d '=' > ./secrets/secret_key
