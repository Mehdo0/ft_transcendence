import asyncio, uuid
from schemas.data import Game, User, GameState
from core.config import ROUND_DURATION, MATCHMAKING_MAX_RANGE, MATCHMAKING_RANGE_STEP, MATCHMAKING_WAIT_PER_STEP
from fastapi import WebSocket
from utils.getters import get_opponents, get_random_word, get_user

class GameManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        
        self.games: dict[str, Game] = {}
        self.player_games: dict[str, str] = {}
        self.lobbies: dict[str, dict] = {}
        
        self.matchmaking_queue: list[str] = []
        self.disconnected_players: list[str] = []
        self.game_timers: dict[str, asyncio.Task] = {}
        self._listeners: dict[str, list] = {}

    def on(self, event: str, callback):
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            asyncio.create_task(cb(event, data))

    
    async def find_player(self, user: User):
        if self.player_games.get(user.username):
            raise ValueError("player is already in a game")
        if user.username in self.matchmaking_queue:
            raise ValueError("player is already in matchmaking")

        print("GAME: player '" + user.username + "' (" + str(user.elo) + " ELO) looking for game...")

        opponent = None
        for search_range in range(MATCHMAKING_RANGE_STEP, MATCHMAKING_MAX_RANGE + 1, MATCHMAKING_RANGE_STEP):
            low = user.elo - search_range
            high = user.elo + search_range

            for _ in range(MATCHMAKING_WAIT_PER_STEP):
                candidates = []
                for queued_name in self.matchmaking_queue:
                    queued_user = get_user(queued_name)
                    if queued_user and low <= queued_user.elo <= high:
                        candidates.append(queued_user)

                if candidates:
                    opponent = min(candidates, key=lambda u: abs(u.elo - user.elo))
                    break

                await asyncio.sleep(1)

            if opponent:
                break

        if opponent:
            self.matchmaking_queue.remove(opponent.username)
            print("\tfound opponent " + opponent.username + " (" + str(opponent.elo) + " ELO)")
            await self.create_game([opponent, user], True)
            return

        print("\tno opponent found, adding to queue")
        self.matchmaking_queue.append(user.username)
        self._emit("broadcast_to_players", payloads=[{
            "username": user.username,
            "payload": {"type": "waiting"}
        }])



    async def create_game(self, players: list[User], is_ranked: bool):
        player_usernames = [player.username for player in players]
        print("GAME: creating game with players: ", player_usernames)
        loop = asyncio.get_running_loop()
        game = Game(
            id=str(uuid.uuid4()),
            game_state=GameState.STARTED,
            players=player_usernames,
            word=get_random_word(),
            is_ranked=is_ranked,
            ends_at=loop.time() + ROUND_DURATION,
        )
        print(
            "game id: ",
            game.id,
            ", word: ",
            game.word,
            ", ranked: ",
            game.is_ranked,
            ", ends_at: ",
            game.ends_at,
        )

        print("creating task for game id ", game.id, "...")

        self.games[game.id] = game

        for player in players:
            game.scores[player.username] = 0
            game.ai_scores[player.username] = 0
            game.score_bonuses[player.username] = 0
            game.round_wins[player.username] = 0
            self.player_games[player.username] = game.id

        payloads = []
        for player in players:
            opponents = get_opponents(player, game)
            payloads.append({
                "username": player.username,
                "payload": {
                    "type": "match_found",
                    "game_id": game.id,
                    "opponent": opponents,
                    "players": player_usernames,
                    "me": player.username,
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                    "is_ranked": game.is_ranked,
                }
            })
        self._emit("broadcast_to_players", payloads=payloads)
        self._emit("game_created", game=game)
