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
	let copied = $state(false);

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
		} else {
			ws.send(JSON.stringify({ type: 'get_lobby', code }));
		}
		ws.addEventListener('message', handleMessage);
	});

	function handleMessage(event: MessageEvent<any>) {
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

	function shortName(name: string, max = 6) {
		return name.length > max ? name.slice(0, max) + '…' : name;
	}

	function startGame() {
		const ws = getWs();
		ws?.send(JSON.stringify({ type: 'start_game', code }));
	}

	function copyCode() {
		if (!code) return;
		navigator.clipboard.writeText(code);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<svelte:head>
	<title>Lobby {code} — Draw Meter</title>
</svelte:head>

<div class="room-container">
	<div class="nb-card room-card">
		<header class="room-header">
			<h1 class="title">Private Game</h1>
			<div class="code-box">
				<span class="code-label">Room Code</span>
				<button class="code-value" onclick={copyCode} title="Click to copy">
					<span class="code-text">{code}</span>
					<span class="code-copy">{copied ? 'Copied ✓' : 'Copy'}</span>
				</button>
			</div>
		</header>

		<div class="players-arena">
			<div class="player-slot">
				{#if players[0]}
					<div class="avatar" title={players[0]}>{shortName(players[0])}</div>
				{:else if isHost}
					<div class="avatar" title={me}>{shortName(me)}</div>
				{:else}
					<div class="avatar empty">?</div>
					<div class="name waiting">Waiting for host…</div>
				{/if}
			</div>

			<div class="vs-badge">VS</div>

			<div class="player-slot">
				{#if players[1]}
					<div class="avatar" title={players[1]}>{shortName(players[1])}</div>
				{:else}
					<div class="avatar empty">?</div>
					<div class="name waiting">Waiting for opponent…</div>
				{/if}
			</div>
		</div>

		<div class="action-footer">
			{#if isHost && players.length === 2}
				<button class="nb-btn nb-btn--primary start-btn" onclick={startGame}>Start game</button>
			{:else if isHost}
				<p class="hint">Waiting for an opponent to join…</p>
			{:else}
				<p class="hint">Waiting for the host to start…</p>
			{/if}
		</div>
	</div>
</div>

<style>
	.room-container {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: var(--space-6) 0;
	}

	.room-card {
		width: 100%;
		max-width: 600px;
		box-shadow: var(--shadow-lg);
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.room-header {
		text-align: center;
	}

	.title {
		margin: 0 0 var(--space-4);
		font-size: var(--fs-2xl);
		text-transform: uppercase;
	}

	.code-box {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-1);
		background: var(--c-bg-alt);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		padding: var(--space-3) var(--space-5);
	}

	.code-label {
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.2em;
		color: var(--c-muted);
	}

	.code-value {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-1);
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		font-family: var(--font-mono);
	}

	.code-text {
		font-size: var(--fs-2xl);
		font-weight: var(--fw-bold);
		letter-spacing: 0.2em;
		color: var(--c-ink);
		text-transform: uppercase;
	}

	.code-copy {
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--c-primary);
	}

	.code-value:hover .code-copy {
		text-decoration: underline;
	}

	.players-arena {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--c-bg-alt);
		border: var(--border);
		padding: var(--space-6) var(--space-5);
	}

	.player-slot {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-3);
		text-align: center;
	}

	.avatar {
		width: 80px;
		height: 80px;
		background: var(--c-primary);
		color: var(--c-on-primary);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 0 var(--space-2);
		font-family: var(--font-display);
		font-size: var(--fs-md);
		font-weight: var(--fw-display);
		text-align: center;
		overflow: hidden;
	}

	.avatar.empty {
		background: var(--c-bg);
		color: var(--c-muted);
		box-shadow: none;
	}

	.name {
		font-family: var(--font-display);
		font-size: var(--fs-lg);
		font-weight: var(--fw-bold);
	}

	.name.waiting {
		color: var(--c-muted);
		font-family: var(--font-body);
		font-weight: var(--fw-regular);
		font-size: var(--fs-sm);
	}

	.vs-badge {
		font-family: var(--font-display);
		font-size: var(--fs-2xl);
		font-weight: var(--fw-display);
		color: var(--c-ink);
		background: var(--c-accent);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		padding: var(--space-1) var(--space-2);
		margin: 0 var(--space-3);
	}

	.action-footer {
		display: flex;
		justify-content: center;
	}

	.start-btn {
		width: 100%;
		height: 56px;
		font-size: var(--fs-lg);
	}

	.hint {
		margin: 0;
		color: var(--c-muted);
		font-size: var(--fs-sm);
		font-style: italic;
	}
</style>
