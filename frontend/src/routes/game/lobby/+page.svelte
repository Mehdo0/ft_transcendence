<script lang="ts">
	import { goto } from "$app/navigation";
    import { getWs, setWs } from "$lib/stores/ws";
    import { game } from "$lib/stores/game";


    function connect1() {
        console.log("Joining lobby...");
        const ws = new WebSocket('/ws/');
        setWs(ws);
        ws.onopen = () => {
			console.log("WebSocket connected");
            ws.send(JSON.stringify({ username: "player1"}));

		};
        ws.onmessage = (event) => {
            console.log("serveur dit:", event.data);
            
            const msg = JSON.parse(event.data);
            if (msg.type === "match_found") {
                console.log("Game found")
                game.id = msg.game_id;
                game.opponent = msg.opponent;
                game.word = msg.word;
                goto("/game/in-game");
            }
        };
        ws.onclose = () => {
            console.log("WebSocket closed");
        };
        ws.onerror = (event) => {
            console.log("WebSocket error:", event);
        };
        
    }
    function connect2() {
        console.log("Joining lobby...");
        const ws = new WebSocket('/ws/');
        setWs(ws);
        ws.onopen = () => {
			console.log("WebSocket connected");
            ws.send(JSON.stringify({ username: "player2"}));

		};
        ws.onmessage = (event) => {
            console.log("serveur dit:", event.data);
            
            const msg = JSON.parse(event.data);
            if (msg.type === "match_found") {
                console.log("Game found")
                game.id = msg.game_id;
                game.opponent = msg.opponent;
                game.word = msg.word;
                goto("/game/in-game");
            }
        };
        ws.onclose = () => {
            console.log("WebSocket closed");
        };
        ws.onerror = (event) => {
            console.log("WebSocket error:", event);
        };
    }

    function findGame() {
        const ws = getWs();
        ws?.send(JSON.stringify({ type: "find_player" }));
    

    }
</script>

<h1>Lobby</h1>
<button onclick={connect1}>Join Lobby</button>
<button onclick={connect2}>Join Lobby</button>
<button onclick={findGame}>Find Game</button>
