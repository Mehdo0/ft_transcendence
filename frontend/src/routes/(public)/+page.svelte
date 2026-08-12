<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { connect, send, subscribe } from '$lib/stores/wsManager';

	let username = $state('');
	let showRejoin = $state(false);
	let rejoinGame = $state({
	opponents: [],
	players: [] as string[],
	time_left: 0,
	is_ranked: false,
	word: '',
	scores: [],
	});

	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_my_score');
		sessionStorage.removeItem('draw_opp_score');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponents');
		sessionStorage.removeItem('draw_players');
		sessionStorage.removeItem('draw_me');
		sessionStorage.removeItem('draw_scores');
		sessionStorage.removeItem('draw_is_ranked');
		sessionStorage.removeItem('draw_ends_at');
		sessionStorage.removeItem('draw_in_progress');
		sessionStorage.removeItem('isHost');
		sessionStorage.removeItem('players');
		sessionStorage.removeItem('draw_opponents');
		sessionStorage.removeItem('draw_round_wins')
	}

	function rejoin() {
		sessionStorage.setItem('draw_word', rejoinGame.word);
		sessionStorage.setItem('draw_opponents', rejoinGame.opponents);
		sessionStorage.setItem('draw_players', JSON.stringify(rejoinGame.players));
		sessionStorage.setItem('draw_me', username);
		sessionStorage.setItem('draw_is_ranked', rejoinGame.is_ranked.toString());
		goto('/in-game');
	}

	function forfeit() {
		send({ type: 'surrender' });
		showRejoin = false;
	}

		onMount(async () => {
			let authenticated = false;
		try {
			const response = await fetch('/api/session/', {
				method: 'GET',
				credentials: 'same-origin'
			});
				const session = await response.json();
				if (session.authenticated && session.user) {
					username = session.user.username;
					authenticated = true;
				}
				} catch {
				return;
				}

				if (!authenticated) return;

				connect();

				let unsub = () => {};
				const timeout = setTimeout(() => unsub(), 3000);

				unsub = subscribe((msg: any) => {
				if (msg.type !== 'reconnect_game') return;
					clearTimeout(timeout);
					unsub();
					rejoinGame = {
						opponents: msg.opponent || [],
						players: msg.players || [],
						time_left: msg.time_left ?? 0,
						is_ranked: msg.is_ranked ?? false,
						word: msg.word || '',
						scores: msg.scores || []
					};
				showRejoin = true;
				});

				return () => {
					clearTimeout(timeout);
					unsub();
				};
				});
		</script>

{#if showRejoin}
 <div class="popup-overlay" role="dialog" aria-label="Game reconnection">
  <div class="popup-card">
   <h2>You have an active game</h2>
   <p>vs {rejoinGame.opponents || rejoinGame.players.filter((p: string) => p !== username).join(', ') || 'opponents'}</p>
   {#if rejoinGame.time_left > 0}
    <p>{Math.ceil(rejoinGame.time_left)}s remaining</p>
   {/if}
   <div class="popup-actions">
    <button class="popup-btn popup-btn--rejoin" onclick={rejoin}>Rejoin</button>
    <button class="popup-btn popup-btn--forfeit" onclick={forfeit}>Surrender</button>
   </div>
  </div>
 </div>
{/if}

<div class="dashboard-wrapper">
	<header class="dashboard-header">
		<p class="eyebrow">Draw Meter</p>
		<h1>Welcome <span class="name-tag">{username || 'Guest'}</span></h1>
		<p class="tagline">Draw fast. Win first. Outsmart the AI.</p>
	</header>

	<main class="menu-card">
		<a href="/start_game" class="menu-tile menu-tile--play">
			<span class="tile-label">Play Now!</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>

		<a href="/lobby" class="menu-tile menu-tile--private">
			<span class="tile-label">Private Game</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>

		<a href="/ranking" class="menu-tile menu-tile--rank">
			<span class="tile-label">Leaderboard</span>
			<span class="tile-arrow" aria-hidden="true">→</span>
		</a>
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

	.menu-tile:hover {
		transform: translate(calc(-1 * var(--nudge)), calc(-1 * var(--nudge)));
		box-shadow: var(--shadow-lg);
	}

	.menu-tile:hover .tile-arrow {
		transform: translateX(var(--space-2));
	}

	.menu-tile:active {
		transform: translate(var(--press), var(--press));
		box-shadow: none;
	}

	@media (max-width: 720px) {
		.dashboard-header h1 {
			font-size: var(--fs-2xl);
		}
	}
		
	.popup-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.7);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
	}

	.popup-card {
	background: var(--c-bg);
	border: var(--border-lg);
	box-shadow: var(--shadow-lg);
	padding: var(--space-7);
	max-width: 400px;
	width: 90%;
	text-align: center;
	}

	.popup-card h2 {
	font-family: var(--font-display);
	font-size: var(--fs-xl);
	text-transform: uppercase;
	margin: 0 0 var(--space-4);
	}

	.popup-card p {
	color: var(--c-muted);
	margin: 0 0 var(--space-2);
	}

	.popup-actions {
	display: flex;
	gap: var(--space-4);
	margin-top: var(--space-6);
	}

	.popup-btn {
	flex: 1;
	padding: var(--space-4);
	font-family: var(--font-display);
	font-size: var(--fs-sm);
	font-weight: var(--fw-bold);
	text-transform: uppercase;
	border: var(--border);
	cursor: pointer;
	transition:
	transform var(--transition),
	box-shadow var(--transition);
	}

	.popup-btn--rejoin {
	background: var(--c-primary);
	color: var(--c-on-primary);
	}

	.popup-btn--forfeit {
	background: var(--c-danger);
	color: var(--c-on-primary);
	}

	.popup-btn:hover {
	transform: translate(calc(-1 * var(--nudge)), calc(-1 * var(--nudge)));
	box-shadow: var(--shadow);
	}

	.popup-btn:active {
	transform: translate(var(--press), var(--press));
	box-shadow: none;
	}

</style>
