	<script lang="ts">
		import { goto } from '$app/navigation';
		import { wsManager } from '$lib/stores/ws';
		import { onMount } from 'svelte';

	let lobbyCode = $state('');

		function send(msg: object) {
			wsManager.send(msg);
		}

		onMount(() => {
			const offLobbyCreated = wsManager.on('lobby_created', (msg) => {
				goto('/lobby/' + msg.code);
			});
			const offLobbyJoined = wsManager.on('lobby_joined', (msg) => {
				goto('/lobby/' + msg.code);
			});

			return () => {
				offLobbyCreated();
				offLobbyJoined();
			};
		});

	function createLobby() {
		send({ type: 'create_lobby' });
	}

	function joinLobby() {
		const code = lobbyCode.trim().toUpperCase();
		if (code.length !== 6 || !code.split('').every((c) => /[A-Z0-9]/.test(c))) return;
		send({ type: 'join_lobby', code });
	}
</script>

<svelte:head>
	<title>Private Match — Draw Meter</title>
</svelte:head>

<div class="private-container">
	<div class="nb-card private-card">
		<h1 class="title">Private Match</h1>
		<p class="subtitle">Play against your friends</p>

		<div class="action-section">
			<div class="action-box">
				<h3>Host a Game</h3>
				<p>Generate a secure room and invite your friends via a secret code.</p>
				<button class="nb-btn nb-btn--primary action-btn" onclick={createLobby}>
					Create Lobby
				</button>
			</div>

			<div class="divider" aria-hidden="true">
				<span>OR</span>
			</div>

			<div class="action-box">
				<h3>Join a Game</h3>
				<p>Enter a secret code provided by the host to join their lobby.</p>

				<div class="input-group">
					<input
						class="nb-input nb-input--mono code-input"
						type="text"
						bind:value={lobbyCode}
						oninput={() =>
							(lobbyCode = lobbyCode
								.toUpperCase()
								.replace(/[^A-Z0-9]/g, '')
								.slice(0, 6))}
						placeholder="AB12C3"
						maxlength="6"
						aria-label="Lobby code"
						onkeydown={(e) => e.key === 'Enter' && joinLobby()}
					/>
					<button
						class="nb-btn nb-btn--accent action-btn"
						onclick={joinLobby}
						disabled={lobbyCode.length !== 6}
					>
						Join
					</button>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.private-container {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: var(--space-6) 0;
	}

	.private-card {
		width: 100%;
		max-width: 760px;
		box-shadow: var(--shadow-lg);
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.title {
		margin: 0;
		font-size: var(--fs-2xl);
		text-align: center;
		text-transform: uppercase;
	}

	.subtitle {
		color: var(--c-muted);
		margin: var(--space-1) 0 var(--space-6);
		font-size: var(--fs-lg);
	}

	.action-section {
		display: flex;
		width: 100%;
		gap: var(--space-5);
		align-items: stretch;
	}

	.action-box {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: var(--space-5);
		background: var(--c-bg-alt);
		border: var(--border);
	}

	h3 {
		margin: 0 0 var(--space-3);
		font-size: var(--fs-xl);
		text-transform: uppercase;
	}

	p {
		color: var(--c-muted);
		font-size: var(--fs-sm);
		line-height: 1.5;
		margin: 0 0 var(--space-5);
	}

	.divider {
		display: flex;
		align-items: center;
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: var(--fs-sm);
		color: var(--c-muted);
	}

	.divider span {
		background: var(--c-bg);
		border: var(--border);
		padding: var(--space-1) var(--space-2);
	}

	.input-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.code-input {
		text-align: center;
		font-size: var(--fs-xl);
	}

	.action-btn {
		width: 100%;
		height: 52px;
	}

	@media (max-width: 768px) {
		.action-section {
			flex-direction: column;
		}
		.divider {
			justify-content: center;
		}
	}
</style>
