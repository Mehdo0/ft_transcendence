# ft_transcendance

## Stack

- Docker: two containers (nginx reverse proxy, backend)
- Reverse proxy: nginx (HTTPS termination, serves built frontend, proxies `/api/`)
- Frontend: SvelteKit (TypeScript, built statically via `adapter-static`)
- Backend: FastAPI
- DB: SQLite

## Architecture

```
[ browser ]
    │  https://localhost
    ▼
[ nginx ]  ── serves built SvelteKit (static files)
    │  http://backend:8000  (internal Docker network)
    ▼
[ backend (FastAPI) ]
```

The `nginx` container is the only one exposed on the host (ports 80, 443).
HTTP traffic on port 80 is redirected to HTTPS.
The TLS certificate is self-signed at image build time.

## Prereqs

Docker + Docker Compose

## Setup

```sh
cp .env.example .env
make
```

## URLs

- https://localhost — application (accept the self-signed certificate warning once)
- http://localhost — redirects to https://localhost

## Makefile

`make` | `make up` | `down` | `logs` | `re` | `fclean`
