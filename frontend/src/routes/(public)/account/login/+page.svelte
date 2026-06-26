<script lang="ts">
	import { login } from '$lib/api';

	let username = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function hashPassword(password: string) {
		const encoder = new TextEncoder();
		const data = encoder.encode(password);

		const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);

		const hashArray = Array.from(new Uint8Array(hashBuffer));
		const hashHex = hashArray.map((byte) => byte.toString(16).padStart(2, '0')).join('');

		return hashHex;
	}

	async function handleLogin(event: Event) {
		event.preventDefault();

		errorMessage = '';
		isLoading = true;

		try {
			const result = await login(username, await hashPassword(password));
			if (!result.ok) {
				errorMessage = result.detail;
				return;
			}
			location.assign('/');
		} catch {
			errorMessage = 'Could not connect to the server.';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Log In — Draw Meter</title>
</svelte:head>

<div class="auth-container">
	<main class="nb-card auth-card">
		<h1 class="title">Welcome Back</h1>
		<p class="subtitle">Log in to play</p>

		{#if errorMessage}
			<div class="error-box" role="alert">
				{errorMessage}
			</div>
		{/if}


		<form onsubmit={handleLogin}>
			<div class="field">
				<label for="username">Username</label>
				<input
					class="nb-input"
					type="text"
					id="username"
					autocomplete="username"
					bind:value={username}
					required
					disabled={isLoading}
				/>
			</div>

			<div class="field">
				<label for="password">Password</label>
				<input
					class="nb-input"
					type="password"
					id="password"
					autocomplete="current-password"
					bind:value={password}
					required
					disabled={isLoading}
				/>
			</div>

			<button type="submit" class="nb-btn nb-btn--primary submit-btn" disabled={isLoading}>
				{isLoading ? 'Logging in...' : 'Log In'}
			</button>
		</form>

		<p class="alt">
			Don't have an account? <a href="/account/register">Register here</a>
		</p>
	</main>
</div>

<style>
	.auth-container {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: var(--space-6) 0;
	}

	.auth-card {
		width: 100%;
		max-width: 420px;
		box-shadow: var(--shadow-lg);
	}

	.title {
		margin: 0 0 var(--space-1);
		font-size: var(--fs-2xl);
		text-transform: uppercase;
	}

	.subtitle {
		margin: 0 0 var(--space-6);
		color: var(--c-muted);
	}

	.error-box {
		background: var(--c-danger);
		color: var(--c-on-danger);
		font-weight: var(--fw-bold);
		font-size: var(--fs-sm);
		padding: var(--space-3) var(--space-4);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		margin-bottom: var(--space-5);
	}

	form {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
		text-align: left;
	}

	label {
		font-family: var(--font-display);
		font-weight: var(--fw-bold);
		font-size: var(--fs-sm);
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}

	.submit-btn {
		width: 100%;
		margin-top: var(--space-2);
	}

	.alt {
		margin: var(--space-6) 0 0;
		font-size: var(--fs-sm);
		color: var(--c-muted);
		text-align: center;
	}

	.alt a {
		font-weight: var(--fw-bold);
	}
</style>
