<script lang="ts">
	import { onMount } from 'svelte';

	// 1. Simple reactive state for the players and errors
	let players = $state([]);
	let errorMessage = $state('');

	// 2. Fetch data directly from your specific endpoint
	onMount(async () => {
		try {
			// Note: Make sure this exactly matches your Python route (no trailing slash)
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
	<title>Leaderboard</title>
	<link
		href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,600"
		rel="stylesheet"
		type="text/css"
	/>
</svelte:head>

<div class="leaderboard-container">
	<h1 class="title">Leaderboard</h1>
	<p class="subtitle">Top 10 Players</p>

	{#if errorMessage}
		<div class="error-box">{errorMessage}</div>
	{/if}

	<!-- Clean, non-interactive list -->
	<ol class="player-list">
		{#each players as player, index}
			<li class="player-row">
				<span class="rank">#{index + 1}</span>
				<span class="name">{player.username}</span>
				<span class="score">{player.elo}</span>
			</li>
		{/each}

		<!-- Optional: Show a message if the database is empty -->
		{#if players.length === 0 && !errorMessage}
			<li class="empty-message">No players ranked yet.</li>
		{/if}
	</ol>
</div>

<style>
	/* Clean, modern, static CSS */
	:global(body) {
		font-family: 'Source Sans Pro', sans-serif;
		background-color: lightblue;
		margin: 0;
		padding: 0;
	}

	.leaderboard-container {
		max-width: 450px;
		margin: 50px auto;
		background: white;
		border-radius: 12px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
		padding: 30px;
		color: #333;
	}

	.title {
		text-align: center;
		margin-top: 0;
		margin-bottom: 5px;
		color: blueviolet;
		font-size: 2em;
	}

	.subtitle {
		text-align: center;
		color: #666;
		margin-top: 0;
		margin-bottom: 25px;
		font-size: 1.1em;
	}

	.player-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.player-row {
		display: flex;
		align-items: center;
		padding: 15px 10px;
		border-bottom: 1px solid #eee;
	}

	/* Remove the border from the last item so it looks clean */
	.player-row:last-child {
		border-bottom: none;
	}

	.rank {
		width: 50px;
		font-weight: 600;
		color: #888;
		font-size: 1.1em;
	}

	.name {
		flex-grow: 1;
		font-weight: 600;
		font-size: 1.2em;
		color: #222;
	}

	.score {
		font-weight: 600;
		color: blueviolet;
		font-size: 1.2em;
	}

	.empty-message {
		text-align: center;
		padding: 20px;
		color: #888;
		font-style: italic;
	}

	.error-box {
		color: red;
		background-color: #fee;
		padding: 12px;
		border-radius: 6px;
		margin-bottom: 20px;
		text-align: center;
		font-weight: 600;
	}
</style>
