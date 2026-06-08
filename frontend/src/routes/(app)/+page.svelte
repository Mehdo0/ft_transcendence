<script lang="ts">
	import { onMount } from 'svelte';

	let loggedIn = $state(false);
	let username = $state('');
	let errorMessage = $state('');

	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_my_score');
		sessionStorage.removeItem('draw_opp_score');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponent');
		sessionStorage.removeItem('isHost');
		sessionStorage.removeItem('players');
	}

	onMount(async () => {
		clearSessionData();
		try {
			const response = await fetch('/api/users/me/', {
				method: 'GET',
				credentials: 'same-origin'
			});

			if (response.ok) {
				const userData = await response.json();
				username = userData.username;
				loggedIn = true;
			} else {
				errorMessage = 'You are not logged in.';
				username = 'Guest';
				loggedIn = false;
			}
		} catch (error) {
			errorMessage = 'Could not connect to the backend server.';
			username = 'Guest';
		}
	});

	async function handleLogout() {
		await fetch('/api/logout', {
			credentials: 'same-origin',
			method: 'POST'
		});
		window.location.reload();
	}
</script>

<div class="dashboard-wrapper">
	<header class="dashboard-header">
		<p class="eyebrow">Draw Meter</p>
		<h1>Welcome <span class="name-tag">{username || '…'}</span></h1>

		{#if errorMessage}
			<div class="error-banner" role="alert">
				{errorMessage}
			</div>
		{:else if loggedIn}
			<p class="tagline">Draw fast. Win first. Outsmart the AI.</p>
		{/if}
	</header>

	<main class="menu-card">
		<a
			href={loggedIn ? '/start_game' : undefined}
			class="menu-tile menu-tile--play"
			class:disabled={!loggedIn}
			aria-disabled={!loggedIn}
		>
			<span class="tile-label">Play Now!</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>

		<a
			href={loggedIn ? '/lobby' : undefined}
			class="menu-tile menu-tile--private"
			class:disabled={!loggedIn}
			aria-disabled={!loggedIn}
		>
			<span class="tile-label">Private Game</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>

		<a href="/ranking" class="menu-tile menu-tile--rank">
			<span class="tile-label">Leaderboard</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>

		{#if !loggedIn}
			<p class="locked-note">
				<a href="/account/login">Log in</a> to start playing.
			</p>
		{/if}
	</main>
</div>

<style>
	.dashboard-wrapper {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-7);
		padding: var(--space-6) 0;
	}

	.dashboard-header {
		text-align: center;
		max-width: 520px;
	}

	.eyebrow {
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.25em;
		color: var(--c-muted);
		margin: 0 0 var(--space-3);
	}

	.dashboard-header h1 {
		font-size: var(--fs-3xl);
		margin: 0;
		text-transform: uppercase;
	}

	.name-tag {
		display: inline-block;
		background: var(--c-accent);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		padding: 0 var(--space-2);
		transform: rotate(-1.5deg);
	}

	.tagline {
		margin: var(--space-4) 0 0;
		color: var(--c-muted);
		font-size: var(--fs-lg);
	}

	.error-banner {
		background: var(--c-danger);
		color: var(--c-on-danger);
		padding: var(--space-3) var(--space-4);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		margin-top: var(--space-4);
		font-weight: var(--fw-bold);
		display: inline-block;
	}

	.menu-card {
		width: 100%;
		max-width: 440px;
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.menu-tile {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--space-4);
		text-decoration: none;
		color: var(--c-ink);
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: var(--fs-xl);
		text-transform: uppercase;
		padding: var(--space-5);
		border: var(--border-lg);
		box-shadow: var(--shadow);
		transition:
			transform var(--transition),
			box-shadow var(--transition);
	}

	.menu-tile--play {
		background: var(--c-primary);
		color: var(--c-on-primary);
	}

	.menu-tile--private {
		background: var(--c-accent);
	}

	.menu-tile--rank {
		background: var(--c-highlight);
		color: var(--c-on-primary);
	}

	.tile-arrow {
		font-size: var(--fs-2xl);
		line-height: 1;
		transition: transform var(--transition);
	}

	.menu-tile:hover:not(.disabled) {
		transform: translate(calc(-1 * var(--nudge)), calc(-1 * var(--nudge)));
		box-shadow: var(--shadow-lg);
	}

	.menu-tile:hover:not(.disabled) .tile-arrow {
		transform: translateX(var(--space-2));
	}

	.menu-tile:active:not(.disabled) {
		transform: translate(var(--press), var(--press));
		box-shadow: none;
	}

	.menu-tile.disabled {
		background: var(--c-bg-alt);
		color: var(--c-muted);
		border-color: var(--c-muted);
		box-shadow: none;
		cursor: not-allowed;
		pointer-events: none;
		transform: none;
	}

	.locked-note {
		text-align: center;
		font-size: var(--fs-sm);
		color: var(--c-muted);
		margin: var(--space-1) 0 0;
	}

	.locked-note a {
		font-weight: var(--fw-bold);
	}

	@media (max-width: 720px) {
		.dashboard-header h1 {
			font-size: var(--fs-2xl);
		}
	}
</style>
