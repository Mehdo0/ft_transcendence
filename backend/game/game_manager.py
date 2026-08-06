import asyncio, uuid
from schemas.data import Game, User, GameState
from core.config import ROUND_DURATION
from fastapi import WebSocket
from utils.getters import get_opponents, get_random_word, get_user

class GameManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {} #preferably put this in ws_manager not here
        
        self.games: dict[str, Game] = {}
        self.player_games: dict[str, str] = {}
        self.lobbies: dict[str, dict] = {}
        
        self.matchmaking_queue: list[str] = []
        self.disconnected_players: dict[str, dict] = {}
        self.game_timers: dict[str, asyncio.Task] = {}



    async def connect(self, user: User, websocket: WebSocket): #move this into ws_manager
        await websocket.accept()
        self.connections[user.username] = websocket
        
        # Handle grace period recovery natively
        if user.username in self.disconnected_players:
            self.disconnected_players[user.username]["reconnected"] = True
            del self.disconnected_players[user.username]

                    
    def get_game_id(self, user: User | None = None) -> str | None:
        if user is None:
            return None

        for game_id, game in self.games.items():
            if user in game.players:
                return game_id

        return None


    def disconnect(self, user: User): #move this into ws manager
        # Only remove the active socket connection. 
        self.connections.pop(user.username, None)
        
        # Pull them out of the queue so they don't match while offline
        if user.username in self.matchmaking_queue:
            self.matchmaking_queue.remove(user.username)



            

    async def broadcast_to_game(self, game_id: str, payload: dict, exclude: str = None): #move this into ws manager
        """Sends a message to everyone in a specific game."""
        game = self.games.get(game_id)
        if not game:
            return
            
        for username in game.players:
            if username == exclude:
                continue
            ws = self.connections.get(username)
            if ws:
                await ws.send_json(payload)




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
            await self.connections[user.username].send_json({"type": "waiting"}) #link this to the ws manager




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
            self.player_self.games[player.username] = game.id
            opponents = get_opponents(player, game)
            print("opponents of player ", player.username, opponents)
            websocket = self.connections[player.username]
            await websocket.send_json(    # move this to the ws manager class 
                {
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
            )
        game.timer = asyncio.create_task(game.timer)
        #self.game_timers[game.id] = asyncio.create_task(self.game_timer(game.id))

manager = GameManager()