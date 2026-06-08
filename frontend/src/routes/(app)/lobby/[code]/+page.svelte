<script lang="ts">
import { goto } from '$app/navigation';
import { getWs, setWs } from '$lib/stores/ws';
import { onMount } from 'svelte';
import { page } from '$app/state';
import { game } from '$lib/stores/game.svelte';
	import { get } from 'svelte/store';

const code = page.params.code;
let players = $state<string[]>([]);
let me = $state('');
let isHost = $state(false);

function clearSessionData() {
        sessionStorage.removeItem('players');
        sessionStorage.removeItem('isHost');
    }

onMount(() => {
	const savedPlayers = sessionStorage.getItem('players');
	if (savedPlayers) players = JSON.parse(savedPlayers);
	
	const savedHost = sessionStorage.getItem('isHost');
	if (savedHost) isHost = savedHost === 'true';

	let ws = getWs();
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        ws = new WebSocket('/ws/');
        setWs(ws);
		ws.onopen = () => {
            ws.send(JSON.stringify({ type: 'get_lobby', code }));
    	};
    } 
	else{
		ws.send(JSON.stringify({ type: 'get_lobby', code }));
		
	}
	ws.addEventListener('message', handleMessage);
});

function handleMessage(event : MessageEvent<any>){
	const msg = JSON.parse(event.data);
	console.log(msg);
	if (msg.type === 'lobby_info') {
		players = msg.players;
		me = msg.me;
		isHost = msg.host === msg.me;
		sessionStorage.setItem('isHost', isHost.toString());
		sessionStorage.setItem('players', JSON.stringify(players));
	}
	if (msg.type === 'player_joined') {
		players = [...players, msg.username];
		sessionStorage.setItem('players', JSON.stringify(players));
	}
	if (msg.type === 'match_found') {
		game.id = msg.game_id;
		game.opponent = msg.opponent;
		game.word = msg.word;
		clearSessionData();
		goto('/game/in-game');
	}
}

function startGame() {
    const ws = getWs();
    ws?.send(JSON.stringify({ type: 'start_game', code }));
}

function copyCode() {
    navigator.clipboard.writeText(code);
	alert("code copied !")
}

</script>

<div class="room-container">
	<div class="room-card">
		<header class="room-header">
			<h1 class="title">Private Game</h1>
			<div class="code-box">
				<span class="code-label">ROOM CODE</span>
				<div class="code-value" onclick={copyCode} title="Click to copy">
					{code}📋
				</div>
			</div>
		</header>

		<div class="players-arena">
			<div class="player-slot">
				{#if players[0]}
					<div class="avatar">P1</div>
					<div class="name">{players[0]}</div>
				{:else if isHost}
					<div class="avatar">P1</div>
					<div class="name">{me}</div>
				{:else}
					<div class="avatar empty">?</div>
					<div class="name waiting">Waiting for host...</div>
				{/if}
			</div>

			<div class="vs-badge">VS</div>

			<div class="player-slot">
				{#if players[1]}
					<div class="avatar">P2</div>
					<div class="name">{players[1]}</div>
				{:else}
					<div class="avatar empty">?</div>
					<div class="name waiting">Waiting for opponent...</div>
				{/if}
			</div>
		</div>

		<div class="action-footer">
			{#if isHost && players.length === 2}
				<button class="menu-btn primary" onclick={startGame}>Start game</button>
			{/if}
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