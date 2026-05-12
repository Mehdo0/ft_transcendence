<script lang="ts">
    import { page } from '$app/stores';
    import { onMount, onDestroy } from 'svelte';
    import { goto } from '$app/navigation';

    // SvelteKit automatically extracts the [code] from the URL folder name!
    const lobbyCode = $page.params.code; 

    // Dynamic state variables
    let players = $state<{ username: string, isReady: boolean }[]>([]);
    let isConnected = $state(false);
    let myStatusReady = $state(false);
    let errorMessage = $state("");
    let ws: WebSocket;

    onMount(() => {
        connectToLobby();
    });

    // Cleanup the WebSocket when the user leaves the page
    onDestroy(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });

    function connectToLobby() {
        const token = localStorage.getItem("access_token");
        if (!token) {
            errorMessage = "You must be logged in to join a lobby.";
            return;
        }

        // Connect to a specific room endpoint on your FastAPI backend
        // Make sure your Python backend has a route like @app.websocket("/ws/lobby/{code}")
        ws = new WebSocket(`wss://localhost/api/ws/lobby/${lobbyCode}?token=${token}`);

        ws.onopen = () => {
            isConnected = true;
            console.log(`Connected to lobby: ${lobbyCode}`);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Handle different messages from the Python backend
            if (data.type === "lobby_state") {
                // Backend sends the current list of players in the room
                players = data.players; 
            } 
            else if (data.type === "game_starting") {
                // Both players are ready, redirect to the actual game canvas!
                goto("/game/in-game");
            }
            else if (data.type === "error") {
                errorMessage = data.message;
            }
        };

        ws.onclose = () => {
            isConnected = false;
        };
    }

    function toggleReady() {
        myStatusReady = !myStatusReady;
        if (ws && ws.readyState === WebSocket.OPEN) {
            // Tell the backend we are ready to play
            ws.send(JSON.stringify({ type: "set_ready", isReady: myStatusReady }));
        }
    }

    function leaveLobby() {
        goto("/game/lobby"); // Send them back to the main match selection
    }

    // Utility function to copy the code to the user's clipboard
    function copyCode() {
        navigator.clipboard.writeText(lobbyCode);
        alert("Lobby code copied to clipboard!");
    }
</script>

<div class="room-container">
    <div class="room-card">
        
        <!-- Header & Code Display -->
        <header class="room-header">
            <h1 class="title">Private Match</h1>
            <div class="code-box">
                <span class="code-label">ROOM CODE</span>
                <!-- svelte-ignore a11y_click_events_have_key_events -->
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div class="code-value" onclick={copyCode} title="Click to copy">
                    {lobbyCode}
                    <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                </div>
            </div>
        </header>

        {#if errorMessage}
            <div class="error-banner">{errorMessage}</div>
        {/if}

        <!-- The Player Slots (Since Ping Pong is 1 vs 1) -->
        <div class="players-arena">
            <!-- Player 1 Slot -->
            <div class="player-slot {players[0]?.isReady ? 'ready' : ''}">
                {#if players[0]}
                    <div class="avatar">P1</div>
                    <div class="name">{players[0].username}</div>
                    <div class="status">{players[0].isReady ? 'READY' : 'WAITING...'}</div>
                {:else}
                    <div class="avatar empty">?</div>
                    <div class="name waiting">Waiting for host...</div>
                {/if}
            </div>

            <div class="vs-badge">VS</div>

            <!-- Player 2 Slot -->
            <div class="player-slot {players[1]?.isReady ? 'ready' : ''}">
                {#if players[1]}
                    <div class="avatar">P2</div>
                    <div class="name">{players[1].username}</div>
                    <div class="status">{players[1].isReady ? 'READY' : 'WAITING...'}</div>
                {:else}
                    <div class="avatar empty">?</div>
                    <div class="name waiting">Waiting for opponent...</div>
                {/if}
            </div>
        </div>

        <!-- Actions -->
        <div class="action-footer">
            <button class="menu-btn secondary" onclick={leaveLobby}>Leave Room</button>
            
            <button 
                class="menu-btn primary {myStatusReady ? 'ready-state' : ''}" 
                onclick={toggleReady}
                disabled={!isConnected}
            >
                {myStatusReady ? 'Cancel Ready' : 'Ready Up'}
            </button>
        </div>

    </div>
</div>

<style>
    .room-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
        padding: 2rem;
    }

    .room-card {
        background-color: white;
        width: 100%;
        max-width: 600px;
        padding: 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    /* --- Header & Code Box --- */
    .room-header {
        text-align: center;
    }

    .title {
        color: blueviolet;
        margin: 0 0 1rem 0;
        font-size: 2.2rem;
    }

    .code-box {
        display: inline-flex;
        flex-direction: column;
        background-color: #f8f9fa;
        border: 2px dashed #ccc;
        border-radius: 8px;
        padding: 10px 20px;
    }

    .code-label {
        font-size: 0.8rem;
        font-weight: bold;
        color: #888;
        letter-spacing: 1px;
    }

    .code-value {
        font-size: 2rem;
        font-weight: bold;
        color: #333;
        letter-spacing: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: color 0.2s;
    }

    .code-value:hover {
        color: blueviolet;
    }

    .copy-icon {
        width: 24px;
        height: 24px;
        opacity: 0.5;
    }

    .error-banner {
        color: red;
        background-color: #fee;
        padding: 1rem;
        border-radius: 6px;
        text-align: center;
        font-weight: bold;
    }

    /* --- Player Arena (The 1v1 Layout) --- */
    .players-arena {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #fafafa;
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #eee;
    }

    .player-slot {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        text-align: center;
    }

    .avatar {
        width: 80px;
        height: 80px;
        background-color: blueviolet;
        color: white;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(138, 43, 226, 0.3);
        transition: all 0.3s ease;
    }

    .avatar.empty {
        background-color: #ddd;
        color: #888;
        box-shadow: none;
        border: 2px dashed #bbb;
    }

    /* Glowing effect when a player is ready */
    .player-slot.ready .avatar {
        background-color: #2ecc71;
        box-shadow: 0 0 20px rgba(46, 204, 113, 0.6);
    }

    .name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
    }

    .name.waiting {
        color: #888;
        font-style: italic;
        font-weight: normal;
    }

    .status {
        font-size: 0.85rem;
        font-weight: bold;
        color: #888;
    }

    .player-slot.ready .status {
        color: #2ecc71;
    }

    .vs-badge {
        font-size: 1.5rem;
        font-weight: 900;
        color: #ccc;
        margin: 0 20px;
        font-style: italic;
    }

    /* --- Footer Actions --- */
    .action-footer {
        display: flex;
        gap: 1rem;
    }

    .menu-btn {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 55px;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: inherit;
    }

    .menu-btn.primary {
        background-color: blueviolet;
        color: white;
        border: none;
    }

    .menu-btn.primary:hover {
        background-color: #7a1cd1;
        transform: translateY(-2px);
    }

    .menu-btn.primary.ready-state {
        background-color: #e74c3c; /* Turns red to indicate "Cancel" */
    }

    .menu-btn.primary.ready-state:hover {
        background-color: #c0392b;
    }

    .menu-btn.secondary {
        background-color: white;
        color: #555;
        border: 3px solid #ddd;
    }

    .menu-btn.secondary:hover {
        background-color: #f0f0f0;
        color: #333;
    }
</style>