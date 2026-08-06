import asyncio, uuid
from schemas.data import Game, User, GameState
from core.config import ROUND_DURATION
from fastapi import WebSocket
from utils.getters import get_opponents, get_random_word, get_user

class GameManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        
        self.games: dict[str, Game] = {}
        self.player_games: dict[str, str] = {}
        self.lobbies: dict[str, dict] = {}
        
        self.matchmaking_queue: list[str] = []
        self.disconnected_players: dict[str, dict] = {}
        self.game_timers: dict[str, asyncio.Task] = {}
        self._listeners: dict[str, list] = {}

    def on(self, event: str, callback):
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(event, data)

    async def find_player(self, user: User):
        if self.player_games.get(user.username):  # player should not be in active game
            raise ValueError("player is already in a game")
        if user.username in self.matchmaking_queue:  # player should not be in queue
            raise ValueError("player is already in matchmaking")

        print("GAME: player '" + user.username + "' is looking for a game...")
        
        if len(self.matchmaking_queue) >= 1:  # another player is already waiting
            print("\tfound another player to match ", user.username, " against!")
            opponent_name = self.matchmaking_queue.pop(0) #maybe add matchmacking logic
            print("\t" + user.username + " vs " + opponent_name)
            assert get_user(opponent_name) is not None
            opponent = get_user(opponent_name)
            assert opponent is not None
            await self.create_game([opponent, user], True)
            return
        else:
            print("\tno player waiting, adding ", user.username, "to queue")
            self.matchmaking_queue.append(user.username)
            self._emit("matchmaking_waiting", user)




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
        self._emit("game_created", game, players)

        for player in players:
            game.scores[player.username] = 0
            game.ai_scores[player.username] = 0
            game.score_bonuses[player.username] = 0
            game.round_wins[player.username] = 0
            self.player_games[player.username] = game.id
            opponents = get_opponents(player, game)
            print("opponents of player ", player.username, opponents)
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
        game.timer = asyncio.create_task(game.timer)
        #self.game_timers[game.id] = asyncio.create_task(self.game_timer(game.id))
