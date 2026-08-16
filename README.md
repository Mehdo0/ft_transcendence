# ft_transcendence

Draw Meter: a real-time multiplayer drawing game. Players race to draw a given word while a transformer-based AI tries to recognize each drawing. The first one to make the AI guess correctly wins. Draw fast, draw clearly, and climb the leaderboard.

## Team

| Role | Member |
| --- | --- |
| Product Owner | mmouaffa |
| Project Manager / Scrum Master | nbonnet |
| Technical Lead / Architect | lfaure |
| Developer | everyone |

## Project Management

- Communication: Discord for daily coordination.
- Task tracking: GitHub PRs for big changes, TODO.md for tracking smaller tasks and bugs
- Meetings: weekly call or in person meet to review progress and blockers.
- Work breakdown:
    - kgiraud: docker setup, frontend.
    - mmouaffa: AI training, backend.
    - nbonnet: AI training, backend + frontend.
    - lfaure: project structure, setup backend, websockets.
    This was how tasks were split at first, as the project moved on, everyone had a chance to work on everything. We all worked on both frontend and backend. No work was fenced off to any team member.
- Code reviews: every significant change was reviewed by at least one other member. We also had devellopment sessions working together on particularly hard features and fixes. Big architectural changes were discussed by all team members.

## Technical Stack

| Layer | Technology | Justification |
| --- | --- | --- |
| Frontend | SvelteKit 5 (Svelte 5, TypeScript, Vite) | Reactive runes, small bundle, fast iteration |
| Backend | FastAPI (Python 3.11) | Async support, typed models, native WebSocket handling |
| Database | SQLite + SQLAlchemy ORM | Zero-config persistence, clear relational schema |
| Real-time | WebSockets | Low-latency game state broadcast between clients |
| Reverse proxy | nginx | HTTPS termination, routing of `/api`, `/ws` and static assets |
| Deployment | Docker + Docker Compose | Single-command declarative environment, caching of layers |

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
- The TLS certificate is self-signed at project initialisation (setup.sh / first make).

## Database Schema

Single `users` table managed by SQLAlchemy ORM:

| Column | Type | Constraints |
| --- | --- | --- |
| username | String | primary key |
| email | String | unique, not null |
| hashed_password | String | not null (bcrypt, salted) |
| elo | Integer | starting at 500 |

## Features

- Authentication: sign up, log in, log out with JWT stored in an httpOnly cookie.
- Password security: bcrypt hashing with random salt, server-side strength validation.
- Matchmaking: ranked 1v1 matchmaking with an expanding ELO range.
- Private lobbies: create or join a lobby with a 6-character code, up to 4 players.
- Real-time gameplay: canvas, live scores, round system with moving win target.
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
| Gaming | AI opponent | Major | 2 |
| AI | Image recognition and tagging (QuickDraw transformer) | Minor | 1 |
| | **Total** | | **14** |

## Individual Contributions

Lucien Faure: implemented major parts of the game and lobby backend, including GameInstance, lobby management and surrender handling; improved authentication, security and WebSocket reliability; refactored the lobby system and fixed edge cases around disconnects, reconnection and invalid games.

Mohamed Mehdi Mouaffak: developed the game manager and matchmaking system, including game-state management and WebSocket communication; implemented and fixed major multiplayer/lobby features such as host departure, surrender, player cleanup and reconnection; also handled backend refactoring, validation, security and dead-code cleanup.

Kim Giraud: focused on frontend gameplay and navigation, implementing navigation guards, WebSocket leave handling and protection against accidental forfeits on page refresh; implemented the server-synchronized round timer and fixed several frontend authentication and navigation issues.

Nils Bonnet: implemented the AI component, including the data pipeline and AI guessing system; integrated AI predictions with the game flow; also worked on ELO, private lobbies and frontend WebSocket management, overcoming connection lifecycle issues across navigation.

## Setup

Prerequisites: Docker and Docker Compose.

```sh
cp .env.example .env
make
```

The `make` command generates the self-signed TLS certificate and starts the containers.

## URLs

- https://localhost:8443 - application (accept the self-signed certificate warning once)
- http://localhost:8080 - redirects to https endpoint

## Makefile targets

`make` (alias `make up`) | `down` | `logs` | `ps` | `re` | `fclean`
