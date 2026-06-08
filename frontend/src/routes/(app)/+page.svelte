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
	<!-- Welcome Header -->
	<header class="dashboard-header">
		<p>Welcome <strong>{username + ' '}</strong>!</p>

		{#if errorMessage}
			<div class="error-banner">
				{errorMessage}
			</div>
		{/if}
	</header>

	<!-- Main Navigation Card -->
	<main class="menu-card">
    <a
        href={loggedIn ? "/start_game" : undefined}
        class="menu-btn"
        class:disabled={!loggedIn}
        aria-disabled={!loggedIn}
    >
        Play Now!
    </a>

    <a
        href={loggedIn ? "/lobby" : undefined}
        class="menu-btn"
        class:disabled={!loggedIn}
        aria-disabled={!loggedIn}
    >
        Private Game
    </a>

    <a href="/ranking" class="menu-btn">
        Leaderboard
    </a>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}

	.dashboard-wrapper {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2rem;
	}

	.dashboard-header {
		text-align: center;
		margin-bottom: 2rem;
		color: #333;
	}

	.error-banner {
		color: red;
		background-color: #fee;
		padding: 1rem;
		border-radius: 6px;
		margin-top: 1rem;
		font-weight: bold;
	}

	/* The Purple Square modernized into a flexbox card */
	.menu-card {
		background-color: blueviolet;
		width: 100%;
		max-width: 400px;
		padding: 2.5rem;
		border-radius: 12px; /* Smoother, modern radius instead of 10% */
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
		display: flex;
		flex-direction: column;
		gap: 1.2rem; /* This creates perfect spacing between buttons automatically */
		box-sizing: border-box;
	}

	/* Anchor tags styled to look exactly like your old buttons */
	.menu-btn {
		display: flex;
		justify-content: center;
		align-items: center;
		background-color: var(--background);
		color: var(--primary);
		text-decoration: none;
		border: 3px solid var(--accent);
		border-radius: 8px;
		height: 50px;
		font-size: 1.1rem;
		font-weight: bold;
		transition: all 0.2s ease;
		cursor: pointer;
	}

	.menu-btn:hover {
		background-color: var(--accent);
		color: var(--text);
		transform: translateY(-2px); /* Slight lift effect on hover */
	}

	.menu-btn.disabled {
		background-color: var(--background);
		color: var(--text);
		border-color: var(--text-muted);
		cursor: not-allowed;
		pointer-events: none;
		transform: none;
	}

	.menu-btn.disabled:hover {
		background-color: var(--background);
		color: var(--text-muted);
	}
</style>
