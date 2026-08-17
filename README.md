*This project has been created as part of the 42 curriculum by kgiraud, lfaure, mmouaffa, nbonnet.*

# ft_transcendence

## Description

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
| Frontend | SvelteKit 2 (Svelte 5, TypeScript, Vite) | Reactive runes, small bundle, fast iteration |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) | Utility-first classes, design tokens declared in `@theme`, only the classes actually used are shipped |
| Backend | FastAPI (Python 3.11) | Async support, typed models, native WebSocket handling |
| Database | SQLite + SQLAlchemy ORM | Zero-config persistence, clear relational schema |
| Real-time | WebSockets | Low-latency game state broadcast between clients |
| Reverse proxy | nginx | HTTPS termination, single exposed entry point, routing of `/api` and `/ws` |
| Deployment | Docker + Docker Compose | Single-command declarative environment, caching of layers |

## Architecture

Three containers behind an nginx reverse proxy:

```
[ browser ]
    |  https://localhost:8443
    v
[ nginx ]  ---------->  [ vite (SvelteKit frontend) :5173 ]
    |                     ^
    | /api  +  /ws        |
    +------------------> [ backend (FastAPI) :8000 ]  <-->  [ SQLite (data/game_data.db) ]
```

- nginx is the only container exposed on the host (ports 8080 and 8443, so the project runs without root).
- HTTP traffic on port 8080 is redirected to HTTPS on 8443.
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

Only the account and its rating are persisted. Games, lobbies and the matchmaking queue live in the backend memory for the duration of a match, so there is a single table and no foreign key relation.

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

## Instructions

Prerequisites: Docker, Docker Compose and ports 8080 and 8443 free.

```sh
cp .env.example .env
make
```

On the first run `make` calls `setup.sh`, which generates the self-signed TLS certificate and the JWT signing key into `secrets/`, then builds and starts the containers.

`.env` holds non-secret configuration only (database path, cookie flags); `.env.example` is the template and `.env` is git-ignored. The JWT signing key is a Docker secret generated into `secrets/`, also git-ignored.

URLs:

- https://localhost:8443 : the application (accept the self-signed certificate warning once)
- http://localhost:8080 : redirects to the https endpoint

Makefile targets: `make` (alias `make up`) | `down` | `logs` | `ps` | `re` | `fclean`

## Resources

- SvelteKit and Svelte 5 runes: https://svelte.dev/docs
- FastAPI, security and WebSockets sections: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org
- PyTorch and the Transformer tutorial: https://pytorch.org/docs
- "Attention Is All You Need", Vaswani et al., 2017: https://arxiv.org/abs/1706.03762
- Google Quick Draw dataset: https://github.com/googlecreativelab/quickdraw-dataset
- Tailwind CSS v4: https://tailwindcss.com/docs
- nginx TLS and WebSocket proxying: https://nginx.org/en/docs
- MDN Canvas API and WebSocket API: https://developer.mozilla.org
- OWASP cheat sheets on password storage and session cookies: https://cheatsheetseries.owasp.org

Use of AI assistants: used as a support tool for looking up documentation, explaining error messages while debugging, writing repetitive frontend styling, and proofreading this README. The architecture, the game logic and the WebSocket protocol were designed and written by the team.
