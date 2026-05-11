<script lang="ts">

    let ws: WebSocket;

    function connect() {
        console.log("Joining lobby...");
        ws = new WebSocket('/ws/');
        ws.onopen = () => {
			console.log("WebSocket connected");
            ws.send(JSON.stringify({ username: "nils" }));

		};
        ws.onmessage = (event) => {
            console.log("serveur dit:", event.data);
        };
        
    }

    function findGame() {
        ws.send(JSON.stringify({ type: "find_player" }));
    

    }
</script>

<h1>Lobby</h1>
<button onclick={connect}>Join Lobby</button>
<button onclick={findGame}>Find Game</button>
