<script lang="ts">
	import { resolve } from '$app/paths';
	import { registerUser, login, hashPassword } from '$lib/api';

	type Errors = {
		username?: string;
		email?: string;
		password?: string;
		confirmPassword?: string;
	};

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let errors = $state<Errors>({});
	let serverError = $state<string | null>(null);
	let loading = $state(false);

	const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

	function validate(): boolean {
		const next: Errors = {};
		if (!username.trim()) next.username = 'Username is required.';
		if (!email.trim()) next.email = 'Email is required.';
		else if (!EMAIL_RE.test(email.trim())) next.email = 'Invalid email address.';
		if (!password) next.password = 'Password is required.';
		if (!confirmPassword) next.confirmPassword = 'Confirmation is required.';
		else if (password !== confirmPassword) next.confirmPassword = 'Passwords do not match.';
		errors = next;
		return Object.keys(next).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		serverError = null;
		if (!validate()) return;

		loading = true;
		try {
			const reg = await registerUser(username.trim(), email.trim(), password);
			if (!reg.ok) {
				serverError = reg.detail;
				return;
			}

			const log = await login(username.trim(), password);
			if (!log.ok) {
				serverError = 'Account created, but automatic login failed. Please go to the login page.';
				return;
			}

			location.assign('/');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register — Draw Meter</title>
</svelte:head>

<div class="auth-container">
	<main class="nb-card auth-card">
		<h1 class="title">Register</h1>
		<p class="subtitle">Join the competition</p>

		{#if serverError}
			<div class="server-error" role="alert">{serverError}</div>
		{/if}

		<form onsubmit={handleSubmit} novalidate>
			<div class="field">
				<label for="username">Username</label>
				<input
					class="nb-input"
					id="username"
					type="text"
					autocomplete="username"
					bind:value={username}
					aria-invalid={!!errors.username}
					aria-describedby={errors.username ? 'username-err' : undefined}
					disabled={loading}
					placeholder="e.g., Vincent du Bocal"
				/>
				{#if errors.username}
					<span class="field-error" id="username-err" aria-live="polite">{errors.username}</span>
				{/if}
			</div>

			<div class="field">
				<label for="email">Email</label>
				<input
					class="nb-input"
					id="email"
					type="email"
					autocomplete="email"
					bind:value={email}
					aria-invalid={!!errors.email}
					aria-describedby={errors.email ? 'email-err' : undefined}
					disabled={loading}
					placeholder="e.g., player@email.com"
				/>
				{#if errors.email}
					<span class="field-error" id="email-err" aria-live="polite">{errors.email}</span>
				{/if}
			</div>

			<div class="field">
				<label for="password">Password</label>
				<input
					class="nb-input"
					id="password"
					type="password"
					autocomplete="new-password"
					bind:value={password}
					aria-invalid={!!errors.password}
					aria-describedby={errors.password ? 'password-err' : undefined}
					disabled={loading}
					placeholder="••••••••"
				/>
				{#if errors.password}
					<span class="field-error" id="password-err" aria-live="polite">{errors.password}</span>
				{/if}
			</div>

			<div class="field">
				<label for="confirm">Confirm Password</label>
				<input
					class="nb-input"
					id="confirm"
					type="password"
					autocomplete="new-password"
					bind:value={confirmPassword}
					aria-invalid={!!errors.confirmPassword}
					aria-describedby={errors.confirmPassword ? 'confirm-err' : undefined}
					disabled={loading}
					placeholder="••••••••"
				/>
				{#if errors.confirmPassword}
					<span class="field-error" id="confirm-err" aria-live="polite"
						>{errors.confirmPassword}</span
					>
				{/if}
			</div>

			<button type="submit" class="nb-btn nb-btn--primary submit-btn" disabled={loading}>
				{loading ? 'Registering...' : 'Register'}
			</button>
		</form>

		<p class="alt">
			Already have an account? <a href={resolve('/account/login')}>Log in</a>
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
		max-width: 460px;
		box-shadow: var(--shadow-lg);
	}

	.title {
		margin: 0 0 var(--space-1);
		font-size: var(--fs-2xl);
		text-align: center;
		text-transform: uppercase;
	}

	.subtitle {
		text-align: center;
		color: var(--c-muted);
		margin: 0 0 var(--space-6);
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
	}

	label {
		font-family: var(--font-display);
		font-weight: var(--fw-bold);
		font-size: var(--fs-sm);
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}

	.nb-input[aria-invalid='true'] {
		border-color: var(--c-danger);
		box-shadow: var(--shadow-sm);
	}

	.field-error {
		color: var(--c-danger);
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
	}

	.server-error {
		background: var(--c-danger);
		color: var(--c-on-danger);
		padding: var(--space-3) var(--space-4);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		margin-bottom: var(--space-5);
		font-size: var(--fs-sm);
		font-weight: var(--fw-bold);
		text-align: center;
	}

	.submit-btn {
		width: 100%;
		margin-top: var(--space-2);
	}

	.alt {
		margin: var(--space-6) 0 0;
		font-size: var(--fs-sm);
		text-align: center;
		color: var(--c-muted);
	}

	.alt a {
		font-weight: var(--fw-bold);
	}
</style>
