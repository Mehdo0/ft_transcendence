# ft_transcendance

## Stack:
    - Docker: two containers (one for frontend one for backend)
    - Frontend: SvelteKit (with Vite for dev and TypseScript)
    - Backend: FastAPI
    - DB: SQLite

## Prereqs

Docker + Docker Compose

## Setup

```sh
cp .env.example .env
make
```

## URLs

- http://localhost:5173 — frontend  
- http://localhost:8000 — backend

## Makefile

`make` | `make up` | `down` | `logs` | `logs-front` | `re`
