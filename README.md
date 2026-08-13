# ft_transcendence

Draw Meter: a real-time multiplayer drawing game. Players race to draw a given word while a transformer-based AI tries to recognize each drawing. Draw fast, draw clearly, and climb the leaderboard.

## Team

| Role | Member |
| --- | --- |
| Product Owner | [Full Name] |
| Project Manager / Scrum Master | [Full Name] |
| Technical Lead / Architect | [Full Name] |
| Developer | [Full Name] |

The team has 4 members, so some members hold multiple roles. Update this table with the actual names and describe each member's responsibilities in one sentence.

## Project Management

- Communication: [Discord / Slack / other] for daily coordination.
- Task tracking: [GitHub Issues / Trello / Notion] for the backlog and sprint planning.
- Meetings: [weekly / bi-weekly] sync to review progress and blockers.
- Work breakdown: features were split into small tasks assigned per member.
- Code reviews: every significant change was reviewed by at least one other member.

## Technical Stack

| Layer | Technology | Justification |
| --- | --- | --- |
| Frontend | SvelteKit 5 (Svelte 5, TypeScript, Vite) | Reactive runes, small bundle, fast iteration |
| Backend | FastAPI (Python 3.11) | Async support, typed models, native WebSocket handling |
| Database | SQLite + SQLAlchemy ORM | Zero-config persistence, clear relational schema |
| Real-time | WebSockets | Low-latency game state broadcast between clients |
| Reverse proxy | nginx | HTTPS termination, routing of `/api`, `/ws` and static assets |
| Deployment | Docker + Docker Compose | Single-command reproducible environment |

## Architecture

Three containers behind an nginx reverse proxy:

```
[ browser ]
    |  https://localhost
    v
[ nginx ]  ---------->  [ vite (SvelteKit frontend) :5173 ]
    |                     ^
    | /api  +  /ws        |
    +------------------> [ backend (FastAPI) :8000 ]  <-->  [ SQLite (data/game_data.db) ]
```

- nginx is the only container exposed on the host (ports 80 and 443).
- HTTP traffic on port 80 is redirected to HTTPS.
- `/api/` and `/ws/` are proxied to the FastAPI backend, with WebSocket upgrade headers.
- Everything else is served by the frontend.
- The TLS certificate is self-signed at startup.

## Database Schema

Single `users` table managed by SQLAlchemy ORM:

| Column | Type | Constraints |
| --- | --- | --- |
| username | String | primary key |
| email | String | unique, not null |
| hashed_password | String | not null (bcrypt, salted) |
| elo | Integer | default 500 |

## Features

- Authentication: sign up, log in, log out with JWT stored in an httpOnly cookie.
- Password security: bcrypt hashing with random salt, server-side strength validation.
- Matchmaking: ranked 1v1 matchmaking with an expanding ELO range.
- Private lobbies: create or join a lobby with a 6-character code, up to 4 players.
- Real-time gameplay: shared canvas, live scores, round system with win target.
- AI recognition: a QuickDraw transformer guesses each drawing and feeds the score.
- Reconnection: disconnected players rejoin the ongoing game during a grace period.
- Surrender: forfeit a match; host exit closes the lobby, non-host exit returns to the lobby.
- Ranking: ELO update after ranked games and a top-10 leaderboard.
- Legal pages: Privacy Policy and Terms of Service.

## Modules

Point calculation: Major = 2 points, Minor = 1 point. Minimum required: 14.

| Category | Module | Type | Points |
| --- | --- | --- | --- |
| Web | Use a framework for frontend and backend (SvelteKit + FastAPI) | Major | 2 |
| Web | Real-time features with WebSockets | Major | 2 |
| Web | Use an ORM (SQLAlchemy) | Minor | 1 |
| Gaming | Complete web-based game | Major | 2 |
| Gaming | Remote players (reconnection, latency handling) | Major | 2 |
| Gaming | Multiplayer game (3+ players) | Major | 2 |
| AI | Image recognition and tagging (QuickDraw transformer) | Minor | 1 |
| | **Total** | | **12** |

Remaining to reach 14 points: OAuth 2.0 (1pt) and Game statistics + match history (1pt), or a tournament system (1pt) and gamification (1pt).

## Individual Contributions

List each member with the specific features, modules and components they implemented, plus any challenges overcome. Example structure:

- [Full Name]: implemented X, Y and Z, fixed the matchmaking queue, etc.
- [Full Name]: implemented A, B and C, built the AI inference pipeline, etc.

## Setup

Prerequisites: Docker and Docker Compose.

```sh
cp .env.example .env
make
```

The `make` command generates the self-signed TLS certificate and starts the containers.

## URLs

- https://localhost - application (accept the self-signed certificate warning once)
- http://localhost - redirects to https://localhost

## Makefile targets

`make` (alias `make up`) | `down` | `logs` | `ps` | `re` | `fclean`
