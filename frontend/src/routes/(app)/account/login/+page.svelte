<script lang="ts">
	import { login } from '$lib/api';

	// Using Svelte 5 reactivity
	let username = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function hashPassword(password: string) {
		// 1. Convert the string password into a byte array
		const encoder = new TextEncoder();
		const data = encoder.encode(password);

		// 2. Ask the browser's built-in Crypto API to hash the bytes using SHA-256
		const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);

		// 3. Convert the resulting ArrayBuffer back into a readable Hexadecimal string
		const hashArray = Array.from(new Uint8Array(hashBuffer));
		const hashHex = hashArray.map((byte) => byte.toString(16).padStart(2, '0')).join('');

		return hashHex;
	}

	async function handleLogin(event: Event) {
		// Prevent the default HTML form submission from refreshing the page
		event.preventDefault();

		errorMessage = '';
		isLoading = true;

		try {
			const result = await login(username, await hashPassword(password));
			if (!result.ok) {
				if (result.status === 401) {
					errorMessage = 'Incorrect username or password.';
				} else {
					errorMessage = 'An error occurred. Please try again later.';
				}
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

<main class="login-container">
	<div class="login-card">
		<h2>Welcome Back</h2>
		<p>Log in to play</p>

		{#if errorMessage}
			<div class="error-box">
				{errorMessage}
			</div>
		{/if}

		<!-- Using the native form onsubmit handles "Enter" key presses automatically -->
		<form onsubmit={handleLogin}>
			<div class="input-group">
				<label for="username">Username</label>
				<!-- bind:value connects the input box directly to our Svelte variable -->
				<input type="text" id="username" bind:value={username} required disabled={isLoading} />
			</div>

			<div class="input-group">
				<label for="password">Password</label>
				<input type="password" id="password" bind:value={password} required disabled={isLoading} />
			</div>

			<button type="submit" disabled={isLoading}>
				{isLoading ? 'Logging in...' : 'Log In'}
			</button>
		</form>

		<div class="register-link">
			Don't have an account? <a href="/account/register">Register here</a>
		</div>
	</div>
</main>

<style>
	/* Centers the card on the screen */
	.login-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 100vh;
		background-color: lightblue;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}

	.login-card {
		background-color: white;
		padding: 2rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		width: 100%;
		max-width: 400px;
		text-align: center;
	}

	h2 {
		margin-top: 0;
		margin-bottom: 0.5rem;
		color: #333;
	}

	p {
		color: #666;
		margin-bottom: 1.5rem;
	}

	.error-box {
		background-color: #fee;
		color: red;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}

	.input-group {
		display: flex;
		flex-direction: column;
		text-align: left;
		margin-bottom: 1.2rem;
	}

	label {
		margin-bottom: 0.5rem;
		font-weight: bold;
		color: #444;
		font-size: 0.9rem;
	}

	input {
		padding: 0.75rem;
		border: 1px solid #ccc;
		border-radius: 6px;
		font-size: 1rem;
	}

	input:focus {
		outline: none;
		border-color: blueviolet;
		box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.2);
	}

	button {
		width: 100%;
		padding: 0.75rem;
		background-color: blueviolet;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		margin-top: 1rem;
		transition: background-color 0.2s;
	}

	button:hover {
		background-color: #7a1cd1;
	}

	button:disabled {
		background-color: #a87bd4;
		cursor: not-allowed;
	}

	.register-link {
		margin-top: 1.5rem;
		font-size: 0.9rem;
		color: #666;
	}

	.register-link a {
		color: blueviolet;
		text-decoration: none;
		font-weight: bold;
	}

	.register-link a:hover {
		text-decoration: underline;
	}
</style>
