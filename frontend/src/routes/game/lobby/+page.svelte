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
        
        try {
            const token = localStorage.getItem("access_token");
            
            // Hitting your requested endpoint to get the secret code
            const response = await fetch('/api/create_lobby', {
                method: 'POST', // Using POST since we are creating a new resource
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                const secretCode = data.code; // Assuming your backend sends { "code": "XYZ123" }
                
                // Route the creator directly to the new lobby room
                goto(`/game/lobby/${secretCode}`);
            } else {
                errorMessage = "Failed to create lobby. Please try again.";
            }
        } catch (error) {
            console.error(error);
            errorMessage = "Could not connect to the server.";
        } finally {
            isCreating = false;
        }
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
    

        if (!cleanCode) {
            errorMessage = "Please enter a valid lobby code.";
            return;
        }

        isJoining = true;
        
        // Route the joining player to the exact same room page.
        // We will build the validation on that specific page next!
        goto(`/game/lobby/${cleanCode}`);
    }
</script>

<h1>Lobby</h1>
<button onclick={connect1}>Join Lobby</button>
<button onclick={connect2}>Join Lobby</button>
<button onclick={findGame}>Find Game</button>
