	<script lang="ts">
		import { onMount } from 'svelte';
		import { goto, beforeNavigate } from '$app/navigation';
		import { isOpen, send, subscribe } from '$lib/stores/wsManager';
		import { game } from '$lib/stores/game.svelte';

	let isConnected = $state(false);
	let isSearching = $state(false);
	let statusMessage = $state('Disconnected');
	let leaving = false;

	beforeNavigate((nav) => {
		if (!isSearching || leaving) return;
		if (nav.willUnload) return;
		if (confirm('Annuler la recherche ?')) {
			send({ type: 'leave' });
		} else {
			nav.cancel();
		}
	});

		function handleMatchFound(msg: any) {
			isSearching = false;
			statusMessage = 'Game found';
			game.id = msg.game_id;
			game.opponent = msg.opponent;
			game.players = msg.players ?? [];
			game.me = msg.me ?? '';
			game.word = msg.word;
			game.scores = {};
			game.is_ranked = msg.is_ranked ?? true;
			sessionStorage.removeItem('private_lobby_code');
			sessionStorage.removeItem('draw_in_progress');
			sessionStorage.setItem(
				'draw_ends_at',
				String(Date.now() + ((msg.duration ?? 60) + (msg.countdown ?? 0)) * 1000)
			);
			leaving = true;
			goto('/in-game');
		}

		async function findGame() {
			send({ type: 'find_player' });
			isSearching = true;
			statusMessage = 'Searching...';
		}
		onMount(() => {
			isConnected = true;
			statusMessage = isOpen() ? 'Connected' : 'Connecting';

			const unsubscribe = subscribe((message) => {
				if (message.type === 'match_found') handleMatchFound(message);
			});

			return () => {
				unsubscribe();
			};
		});
	</script>

<svelte:head>
	<title>Matchmaking — Draw Meter</title>
</svelte:head>

<div class="lobby-container">
	<div class="nb-card lobby-card">
		<h1 class="title">Matchmaking</h1>

		<div class="status-box" class:connected={isConnected} class:searching={isSearching}>
			<span class="status-dot"></span>
			<span class="status-text">{statusMessage}</span>
		</div>

		<button
			class="nb-btn nb-btn--primary find-btn"
			onclick={findGame}
			disabled={!isConnected || isSearching}
		>
			{isSearching ? 'Searching…' : 'Find Game'}
		</button>
	</div>
</div>

<style>
	.lobby-container {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: var(--space-6) 0;
	}

	.lobby-card {
		width: 100%;
		max-width: 440px;
		box-shadow: var(--shadow-lg);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-6);
	}

	.title {
		margin: 0;
		font-size: var(--fs-2xl);
		text-align: center;
		text-transform: uppercase;
	}

	.status-box {
		display: inline-flex;
		align-items: center;
		gap: var(--space-3);
		background: var(--c-bg-alt);
		padding: var(--space-2) var(--space-4);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		font-family: var(--font-mono);
		font-weight: var(--fw-bold);
		font-size: var(--fs-sm);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.status-dot {
		width: 12px;
		height: 12px;
		background: var(--c-muted);
		border: 2px solid var(--c-ink);
	}

	.status-box.connected .status-dot {
		background: var(--c-success);
	}

	.status-box.searching .status-dot {
		background: var(--c-accent);
		animation: blink 1s steps(2, start) infinite;
	}

	@keyframes blink {
		50% {
			background: var(--c-highlight);
		}
	}

	.find-btn {
		width: 100%;
		height: 56px;
		font-size: var(--fs-lg);
	}

	@media (prefers-reduced-motion: reduce) {
		.status-box.searching .status-dot {
			animation: none;
		}
	}
</style>
