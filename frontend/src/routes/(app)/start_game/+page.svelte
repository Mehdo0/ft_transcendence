<script lang="ts">
	// Added state variables to make the UI react to the connection
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getWs } from '$lib/stores/ws';
	import { game } from '$lib/stores/game.svelte';

	let isConnected = $state(false);
	let isSearching = $state(false);
	let statusMessage = $state('Disconnected');

	function connect() {
        const ws = getWs();
        if (!ws) return;
		if (ws.readyState === WebSocket.OPEN) {
        	isConnected = true;
        	statusMessage = 'Connected';
    	}
		ws.onmessage = (event) => {
			console.log('serveur dit:', event.data);
			const msg = JSON.parse(event.data);
			if (msg.type === 'match_found') {
				isSearching = false;
				statusMessage = 'Game found';
				console.log('Game found');
				game.id = msg.game_id;
				game.opponent = msg.opponent;
				game.word = msg.word;
				goto('/game/in-game');
			}
		};
		ws.onclose = () => {
			console.log('WebSocket closed');
			isConnected = false;
			statusMessage = 'Disconnected';
		};
		ws.onerror = (event) => {
			console.log('WebSocket error:', event);
			isConnected = false;
			statusMessage = 'Error';
		};
	}

	function findGame() {
		const ws = getWs();
		ws?.send(JSON.stringify({ type: 'find_player' }));
		isSearching = true;
		statusMessage = 'Searching...';
	}
	onMount(() => {
		connect();
	});
</script>

<div class="lobby-container">
	<div class="lobby-card">
		<h1 class="title">Matchmaking</h1>

		<div class="status-box" class:connected={isConnected} class:searching={isSearching}>
			<span class="status-dot"></span>
			<span class="status-text">{statusMessage}</span>
		</div>

		<div class="button-group">
			<button class="menu-btn secondary" onclick={findGame} disabled={!isConnected || isSearching}>
				{isSearching ? 'Searching...' : 'Find Game'}
			</button>
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
		0% {
			transform: scale(0.95);
			opacity: 0.8;
			box-shadow: 0 0 0 0 rgba(241, 196, 15, 0.7);
		}
		70% {
			transform: scale(1.1);
			opacity: 1;
			box-shadow: 0 0 0 10px rgba(241, 196, 15, 0);
		}
		100% {
			transform: scale(0.95);
			opacity: 0.8;
			box-shadow: 0 0 0 0 rgba(241, 196, 15, 0);
		}
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
