<script lang="ts">
    // Added state variables to make the UI react to the connection
    let isConnected = $state(false);
    let isSearching = $state(false);
    let statusMessage = $state("Disconnected");
    let ws: WebSocket;

    function connect() {
        console.log("Joining lobby...");
        statusMessage = "Connecting to server...";
        
        // Note: ensure this URL matches your setup (e.g., wss://localhost/api/ws)
        ws = new WebSocket('/ws/');
        
        ws.onopen = () => {
            console.log("WebSocket connected");
            isConnected = true;
            statusMessage = "Connected to Lobby";
            
            // Note: You should eventually replace "nils" with your actual username variable!
            ws.send(JSON.stringify({ username: "nils" })); 
        };
        
        ws.onmessage = (event) => {
            console.log("Server says:", event.data);
            
            // Example: update UI if the backend confirms a game is found
            if (event.data.includes("found")) {
                isSearching = false;
                statusMessage = "Game Found! Get ready...";
            }
        };

        ws.onclose = () => {
            isConnected = false;
            isSearching = false;
            statusMessage = "Disconnected from server";
        };
    }

    function findGame() {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        
        isSearching = true;
        statusMessage = "Searching for an opponent...";
        ws.send(JSON.stringify({ type: "find_player" }));
    }
</script>

<div class="lobby-container">
    <div class="lobby-card">
        <h1 class="title">Matchmaking</h1>
        
        <!-- Status Indicator (Dot changes color based on state) -->
        <div class="status-box" class:connected={isConnected} class:searching={isSearching}>
            <span class="status-dot"></span>
            <span class="status-text">{statusMessage}</span>
        </div>

        <div class="button-group">
            <!-- Dynamically show the right button based on connection -->
            {#if !isConnected}
                <button class="menu-btn primary" onclick={connect}>
                    Join Lobby
                </button>
            {:else}
                <button class="menu-btn secondary" onclick={findGame} disabled={isSearching}>
                    {isSearching ? 'Searching...' : 'Find Game'}
                </button>
            {/if}
        </div>
    </div>
</div>

<style>
    .lobby-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh; /* Keeps it perfectly centered on the screen */
        padding: 2rem;
    }

    .lobby-card {
        background-color: white;
        width: 100%;
        max-width: 450px;
        padding: 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2rem;
    }

    .title {
        color: blueviolet;
        margin: 0;
        font-size: 2.5rem;
        text-align: center;
    }

    /* --- Status Indicator Styling --- */
    .status-box {
        display: flex;
        align-items: center;
        gap: 12px;
        background-color: #f8f9fa;
        padding: 12px 24px;
        border-radius: 30px;
        font-weight: 600;
        color: #555;
        border: 1px solid #eee;
        transition: all 0.3s ease;
    }

    .status-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: #ccc; /* Default grey */
        transition: background-color 0.3s ease;
    }

    /* Turn dot green when connected */
    .status-box.connected .status-dot {
        background-color: #2ecc71; 
    }

    /* Turn dot yellow and pulsate when searching */
    .status-box.searching .status-dot {
        background-color: #f1c40f; 
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(241, 196, 15, 0.7); }
        70% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 10px rgba(241, 196, 15, 0); }
        100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(241, 196, 15, 0); }
    }

    /* --- Button Styling --- */
    .button-group {
        width: 100%;
        display: flex;
        flex-direction: column;
    }

    .menu-btn {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 60px;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: inherit;
    }

    .menu-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .menu-btn.primary {
        background-color: blueviolet;
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(138, 43, 226, 0.3);
    }

    .menu-btn.primary:hover:not(:disabled) {
        background-color: #7a1cd1;
        transform: translateY(-2px);
    }

    .menu-btn.secondary {
        background-color: white;
        color: blueviolet;
        border: 3px solid aquamarine;
    }

    .menu-btn.secondary:hover:not(:disabled) {
        background-color: aquamarine;
        color: #333;
        transform: translateY(-2px);
    }
</style>