<script lang="ts">
	import { onMount } from 'svelte';

	type Player = { username: string; elo: number };

	let players = $state<Player[]>([]);
	let me = $state('');
	let errorMessage = $state('');

	onMount(async () => {
		try {
			const meRes = await fetch('/api/users/me/', { credentials: 'same-origin' });
			if (meRes.ok) me = (await meRes.json()).username;
		} catch {
			// not logged in — no highlighting
		}

		try {
			const res = await fetch('/api/get_ranking');

			if (res.ok) {
				players = await res.json();
			} else {
				errorMessage = 'Failed to load leaderboard.';
			}
		} catch (e) {
			console.error('Failed to load leaderboard', e);
			errorMessage = 'Could not connect to the server.';
		}
	});
</script>

<svelte:head>
	<title>Leaderboard — Draw Meter</title>
</svelte:head>

<div class="leaderboard-container">
	<div class="nb-card leaderboard-card">
		<header class="board-header">
			<h1 class="title">Leaderboard</h1>
			<p class="subtitle">Top 10 Players</p>
		</header>

		{#if errorMessage}
			<div class="error-box" role="alert">{errorMessage}</div>
		{/if}

		<ol class="player-list">
			{#each players as player, index (player.username)}
				<li
					class="player-row"
					class:top={index < 3}
					class:rank-1={index === 0}
					class:rank-2={index === 1}
					class:rank-3={index === 2}
					class:is-me={me && player.username === me}
				>
					<span class="rank">{index + 1}</span>
					<span class="name">
						{player.username}
						{#if me && player.username === me}<span class="you-tag">You</span>{/if}
					</span>
					<span class="score">{player.elo}</span>
				</li>
			{/each}

			{#if players.length === 0 && !errorMessage}
				<li class="empty-message">No players ranked yet.</li>
			{/if}
		</ol>
	</div>
</div>

<style>
	.leaderboard-container {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: flex-start;
		padding: var(--space-6) 0;
	}

	.leaderboard-card {
		width: 100%;
		max-width: 480px;
		box-shadow: var(--shadow-lg);
	}

	.board-header {
		text-align: center;
		margin-bottom: var(--space-5);
	}

	.title {
		margin: 0 0 var(--space-1);
		font-size: var(--fs-2xl);
		text-transform: uppercase;
	}

	.subtitle {
		margin: 0;
		color: var(--c-muted);
		font-family: var(--font-mono);
		font-size: var(--fs-sm);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.player-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.player-row {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3);
		border: var(--border);
		background: var(--c-bg);
	}

	.player-row.top {
		box-shadow: var(--shadow-sm);
	}

	.player-row.top .rank {
		color: var(--c-ink);
	}

	.player-row.rank-1 .rank {
		background: var(--c-accent);
	}
	.player-row.rank-2 .rank {
		background: var(--c-silver);
	}
	.player-row.rank-3 .rank {
		background: var(--c-highlight);
		color: var(--c-on-primary);
	}

	.player-row.is-me {
		border-color: var(--c-primary);
		box-shadow: var(--shadow-accent);
	}

	.rank {
		flex-shrink: 0;
		width: 2.25rem;
		height: 2.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: var(--fs-base);
		color: var(--c-muted);
		background: var(--c-bg-alt);
		border: var(--border);
	}

	.name {
		flex-grow: 1;
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-family: var(--font-display);
		font-weight: var(--fw-bold);
		font-size: var(--fs-lg);
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.you-tag {
		flex-shrink: 0;
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--c-on-primary);
		background: var(--c-primary);
		border: 2px solid var(--c-ink);
		padding: 0 var(--space-2);
	}

	.score {
		flex-shrink: 0;
		font-family: var(--font-mono);
		font-weight: var(--fw-bold);
		font-size: var(--fs-lg);
		font-variant-numeric: tabular-nums;
	}

	.empty-message {
		text-align: center;
		padding: var(--space-5);
		color: var(--c-muted);
		font-style: italic;
	}

	.error-box {
		background: var(--c-danger);
		color: var(--c-on-danger);
		padding: var(--space-3) var(--space-4);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		margin-bottom: var(--space-5);
		text-align: center;
		font-weight: var(--fw-bold);
	}
</style>
