<script lang="ts">

    let ws: WebSocket;

    function connect() {
        console.log("Joining lobby...");
        ws = new WebSocket('/ws/');
        ws.onopen = () => {
			console.log("WebSocket connected");
            ws.send("salut bg");

		};
        ws.onmessage = (event) => {
            console.log("serveur dit:", event.data, event.type, event.origin);
        };
        
    }

    function findGame() {
    

    }
</script>

<h1>Lobby</h1>
<button onclick={connect}>Join Lobby</button>
<button onclick={findGame}>Find Game</button>
