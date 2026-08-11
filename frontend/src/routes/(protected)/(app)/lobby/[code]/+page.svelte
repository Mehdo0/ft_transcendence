<script lang="ts">
	import { send, subscribe } from '$lib/stores/wsManager';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { game } from '$lib/stores/game.svelte';
	import { goto, beforeNavigate } from '$app/navigation';


	const code = page.params.code ?? '';
	let players = $state<string[]>([]);
	let me = $state('');
	let isHost = $state(false);
	let copied = $state(false);
	let leaving = false;

	beforeNavigate((nav) => {
		if (leaving) return;
		if (nav.willUnload) return;
		if (confirm('Quitter le lobby ?')) {
			send({ type: 'leave' });
		} else {
			nav.cancel();
		}
	});

	function clearSessionData() {
		sessionStorage.removeItem('players');
		sessionStorage.removeItem('isHost');
	}

		onMount(() => {
			const savedPlayers = sessionStorage.getItem('players');
			if (savedPlayers) {
				try {
					players = JSON.parse(savedPlayers);
				} catch {
					players = [];
				}
			}

			const savedHost = sessionStorage.getItem('isHost');
			if (savedHost) isHost = savedHost === 'true';

			const unsubscribe = subscribe(handleMessage);

			send({ type: 'get_lobby', code });

			return () => {
				unsubscribe();
			};
		});

		function handleMessage(msg: any) {
		if (msg.type === 'lobby_info') {
			players = msg.players;
			me = msg.me;
			isHost = msg.host === msg.me;
			sessionStorage.setItem('isHost', isHost.toString());
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'player_joined') {
			if (!players.includes(msg.username)) players = [...players, msg.username];
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'player_left') {
			players = players.filter((player) => player !== msg.username);
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'lobby_closed') {
			clearSessionData();
			leaving = true;
			goto('/lobby');
		}
		if (msg.type === 'match_found') {
			game.id = msg.game_id;
			game.opponent = msg.opponent[0] ?? '';
			game.players = msg.players ?? [];
			game.me = msg.me ?? '';
			game.word = msg.word;
			game.scores = {};
			game.is_ranked = msg.is_ranked ?? false;
			clearSessionData();
			sessionStorage.setItem('private_lobby_code', code);
			sessionStorage.removeItem('draw_in_progress');
			sessionStorage.setItem(
				'draw_ends_at',
				String(Date.now() + ((msg.duration ?? 60) + (msg.countdown ?? 0)) * 1000)
			);
			leaving = true;
			goto('/in-game');
		}
	}

	function shortName(name: string, max = 6) {
		return name.length > max ? name.slice(0, max) + '…' : name;
	}

			function startGame() {
				send({ type: 'start_game', code });
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
			{#each players as player (player)}
				<div class="player-slot">
					<div class="avatar" title={player}>{shortName(player)}</div>
				</div>
			{/each}
		</div>

		<div class="action-footer">
			{#if isHost}
				<button
					class="nb-btn nb-btn--primary start-btn"
					onclick={startGame}
					disabled={players.length < 2}
				>
					{players.length < 2 ? 'Waiting for players…' : 'Start game'}
				</button>
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
		justify-content: center;
		flex-wrap: wrap;
		gap: var(--space-4);
		background: var(--c-bg-alt);
		border: var(--border);
		padding: var(--space-6) var(--space-5);
	}

	.player-slot {
		flex: 0 0 96px;
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
