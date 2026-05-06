# to be ran only once on repo clone

mkdir secrets
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout ./secrets/server.key \
  -out ./secrets/server.crt \
  -subj "/C=CH/ST=Vaud/L=Lausanne/O=42/CN=localhost"

