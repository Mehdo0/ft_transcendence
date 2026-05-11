<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { registerUser, login } from '$lib/api';

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
		if (!username.trim()) next.username = 'Nom d’utilisateur requis.';
		if (!email.trim()) next.email = 'Email requis.';
		else if (!EMAIL_RE.test(email.trim())) next.email = 'Email invalide.';
		if (!password) next.password = 'Mot de passe requis.';
		if (!confirmPassword) next.confirmPassword = 'Confirmation requise.';
		else if (password !== confirmPassword)
			next.confirmPassword = 'Les mots de passe ne correspondent pas.';
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
				if (reg.status === 406) serverError = 'Ce nom d’utilisateur est déjà pris.';
				else serverError = 'Inscription impossible, réessaie.';
				return;
			}

			const log = await login(username.trim(), password);
			if (!log.ok) {
				serverError = 'Compte créé, mais connexion automatique échouée. Va sur la page de login.';
				return;
			}

			await goto(resolve('/'));
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Inscription</title>
</svelte:head>

<main class="page">
	<h1>Inscription</h1>

	{#if serverError}
		<div class="server-error" role="alert">{serverError}</div>
	{/if}

	<form onsubmit={handleSubmit} novalidate>
		<div class="field">
			<label for="username">Nom d’utilisateur</label>
			<input
				id="username"
				type="text"
				autocomplete="username"
				bind:value={username}
				aria-invalid={!!errors.username}
				aria-describedby={errors.username ? 'username-err' : undefined}
				disabled={loading}
			/>
			{#if errors.username}
				<span class="field-error" id="username-err" aria-live="polite">{errors.username}</span>
			{/if}
		</div>

		<div class="field">
			<label for="email">Email</label>
			<input
				id="email"
				type="email"
				autocomplete="email"
				bind:value={email}
				aria-invalid={!!errors.email}
				aria-describedby={errors.email ? 'email-err' : undefined}
				disabled={loading}
			/>
			{#if errors.email}
				<span class="field-error" id="email-err" aria-live="polite">{errors.email}</span>
			{/if}
		</div>

		<div class="field">
			<label for="password">Mot de passe</label>
			<input
				id="password"
				type="password"
				autocomplete="new-password"
				bind:value={password}
				aria-invalid={!!errors.password}
				aria-describedby={errors.password ? 'password-err' : undefined}
				disabled={loading}
			/>
			{#if errors.password}
				<span class="field-error" id="password-err" aria-live="polite">{errors.password}</span>
			{/if}
		</div>

		<div class="field">
			<label for="confirm">Confirmer le mot de passe</label>
			<input
				id="confirm"
				type="password"
				autocomplete="new-password"
				bind:value={confirmPassword}
				aria-invalid={!!errors.confirmPassword}
				aria-describedby={errors.confirmPassword ? 'confirm-err' : undefined}
				disabled={loading}
			/>
			{#if errors.confirmPassword}
				<span class="field-error" id="confirm-err" aria-live="polite">{errors.confirmPassword}</span
				>
			{/if}
		</div>

		<button type="submit" class="submit" disabled={loading}>
			{loading ? 'Inscription...' : 'S’inscrire'}
		</button>
	</form>

	<p class="alt">
		Déjà un compte ? <a href={resolve('/account/login')}>Connecte-toi</a>
	</p>
</main>

<style>
	.page {
		max-width: 400px;
		margin: 3rem auto;
		padding: 0 1rem;
		font-family: system-ui, sans-serif;
	}

	h1 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	label {
		font-size: 0.9rem;
		font-weight: 500;
	}

	input {
		padding: 0.5rem 0.6rem;
		border: 1px solid #cbd2d9;
		border-radius: 4px;
		font-size: 1rem;
		background: white;
	}

	input:focus {
		outline: 2px solid #3b82f6;
		outline-offset: 1px;
		border-color: #3b82f6;
	}

	input[aria-invalid='true'] {
		border-color: #dc2626;
	}

	input:disabled {
		background: #f3f4f6;
		cursor: not-allowed;
	}

	.field-error {
		color: #dc2626;
		font-size: 0.85rem;
	}

	.server-error {
		background: #fee2e2;
		border: 1px solid #dc2626;
		color: #7f1d1d;
		padding: 0.6rem 0.8rem;
		border-radius: 4px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.submit {
		margin-top: 0.5rem;
		padding: 0.65rem;
		background: #1f2937;
		color: white;
		border: none;
		border-radius: 4px;
		font-size: 1rem;
		cursor: pointer;
	}

	.submit:hover:not(:disabled) {
		background: #111827;
	}

	.submit:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.alt {
		margin-top: 1.5rem;
		font-size: 0.9rem;
		text-align: center;
	}

	.alt a {
		color: #3b82f6;
	}
</style>
