<script lang="ts">
    import { goto } from '$app/navigation';
    import { getWs, setWs } from '$lib/stores/ws';
	import { onMount } from 'svelte';

    let lobbyCode = $state('');

    onMount(() => {
		console.log('connecting...');
		const ws = new WebSocket('/ws/');
		setWs(ws);
		ws.onopen = () => {
			console.log('WebSocket connected');
		};
		ws.onmessage = (event) => {
			console.log('serveur dit:', event.data);
			const msg = JSON.parse(event.data);
			if (msg.type === 'lobby_details') {
				let code = msg.code;
				goto('/game/lobby/' + code);
			}
		};
		ws.onclose = () => {
			console.log('WebSocket closed');
		};
		ws.onerror = (event) => {
			console.log('WebSocket error:', event);
		};
    })

    function createLobby() {
        let ws = getWs();
        ws?.send(JSON.stringify({ type: 'create_lobby' }));
    }

    function joinLobby() {
        const code = lobbyCode.trim(); //a fix pour eviter injection, mauvais format etc
        let ws = getWs();
        ws?.send(JSON.stringify({type: 'join_lobby', code}));
    }
</script>

<h1>Lobby</h1>
<button onclick={createLobby}>Create a Lobby</button>
<input
    type="text"
    bind:value={lobbyCode}
    maxlength="6"
    placeholder="enter lobby code,ex. 123456"
    
/>
<button onclick={joinLobby}>Join a Lobby (entry 6 digits code)</button> 

<!-- <div class="private-container">
    <div class="private-card">
        <h1 class="title">Private Match</h1>
        <p class="subtitle">Play against your friends</p>

        {#if errorMessage}
            <div class="error-banner">{errorMessage}</div>
        {/if}

        <div class="action-section">
            <div class="create-box">
                <h3>Host a Game</h3>
                <p>Generate a secure room and invite your friends via a secret code.</p>
                <button class="menu-btn primary" onclick={createLobby} disabled={isCreating}>
                    {isCreating ? 'Generating...' : 'Create Lobby'}
                </button>
            </div>

            <div class="divider-vertical"></div>
            <hr class="divider-horizontal" />

            <div class="join-box">
                <h3>Join a Game</h3>
                <p>Enter a secret code provided by the host to join their lobby.</p>

                <div class="input-group">
                    <input
                        type="text"
                        bind:value={joinCode}
                        placeholder="e.g. A7X9B"
                        maxlength="8"
                        onkeydown={(e) => e.key === 'Enter' && joinLobby()}
                    />
                    <button class="menu-btn secondary" onclick={joinLobby} disabled={isJoining || !joinCode}>
                        {isJoining ? 'Joining...' : 'Join'}
                    </button>
                </div>
            </div>
        </div>
    </div>
</div> -->

<!-- <style>
    .private-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
        padding: 2rem;
    }

    .private-card {
        background-color: white;
        width: 100%;
        max-width: 800px;
        padding: 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .title {
        color: blueviolet;
        margin: 0;
        font-size: 2.5rem;
        text-align: center;
    }

    .subtitle {
        color: #666;
        margin-top: 5px;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }

    .error-banner {
        color: red;
        background-color: #fee;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 2rem;
        width: 100%;
        text-align: center;
        font-weight: bold;
        box-sizing: border-box;
    }

    .action-section {
        display: flex;
        width: 100%;
        gap: 2rem;
        align-items: stretch;
    }

    .create-box, .join-box {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 12px;
        border: 1px solid #eee;
    }

    h3 {
        color: #333;
        margin-top: 0;
        font-size: 1.4rem;
    }

    p {
        color: #666;
        font-size: 0.95rem;
        line-height: 1.4;
        margin-bottom: 1.5rem;
    }

    .divider-vertical {
        width: 1px;
        background-color: #ddd;
    }

    .divider-horizontal {
        display: none;
        border: 0;
        height: 1px;
        background-color: #ddd;
        width: 100%;
        margin: 1rem 0;
    }

    .input-group {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    input[type="text"] {
        padding: 12px 15px;
        font-size: 1.2rem;
        border: 2px solid #ccc;
        border-radius: 8px;
        outline: none;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-family: inherit;
        transition: border-color 0.2s;
    }

    input[type="text"]:focus {
        border-color: blueviolet;
    }

    .menu-btn {
        width: 100%;
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

    .menu-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .menu-btn.primary {
        background-color: blueviolet;
        color: white;
        border: none;
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

    @media (max-width: 768px) {
        .action-section {
            flex-direction: column;
        }
        .divider-vertical {
            display: none;
        }
        .divider-horizontal {
            display: none;
        }
    }
</style> -->