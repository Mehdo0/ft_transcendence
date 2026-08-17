<script lang="ts">
	import { resolve } from '$app/paths';
	import { registerUser, login } from '$lib/api';
	import Button from '$lib/components/Button.svelte';
	import ErrorBox from '$lib/components/ErrorBox.svelte';
	import Input from '$lib/components/Input.svelte';
	import PageTitle from '$lib/components/PageTitle.svelte';

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

	const labelClasses = 'font-display text-sm font-bold tracking-[0.02em] uppercase';
	const errorClasses = 'font-mono text-xs font-bold text-danger';
	const invalidClasses = 'aria-[invalid=true]:border-danger';

	function validate(): boolean {
		const next: Errors = {};
		if (!username.trim()) next.username = 'Username is required.';
		else if (!/^[a-zA-Z0-9]+$/.test(username.trim())) next.username = 'Only a-z, A-Z and 0-9 charaters.';
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

<div class="flex flex-1 items-center justify-center py-8">
	<main class="w-full max-w-[460px] border-4 border-ink bg-bg p-6 shadow-nb-lg">
		<PageTitle title="Register" subtitle="Join the competition" class="mb-8 text-center" />

		{#if serverError}
			<ErrorBox class="mb-6 text-center">{serverError}</ErrorBox>
		{/if}

		<form onsubmit={handleSubmit} novalidate class="flex flex-col gap-6">
			<div class="flex flex-col gap-2">
				<label for="username" class={labelClasses}>Username</label>
				<Input
					id="username"
					type="text"
					autocomplete="username"
					bind:value={username}
					aria-invalid={!!errors.username}
					aria-describedby={errors.username ? 'username-err' : undefined}
					disabled={loading}
					placeholder="e.g., Vincent du Bocal"
					class={invalidClasses}
				/>
				{#if errors.username}
					<span class={errorClasses} id="username-err" aria-live="polite">{errors.username}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="email" class={labelClasses}>Email</label>
				<Input
					id="email"
					type="email"
					autocomplete="email"
					bind:value={email}
					aria-invalid={!!errors.email}
					aria-describedby={errors.email ? 'email-err' : undefined}
					disabled={loading}
					placeholder="e.g., player@email.com"
					class={invalidClasses}
				/>
				{#if errors.email}
					<span class={errorClasses} id="email-err" aria-live="polite">{errors.email}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="password" class={labelClasses}>Password</label>
				<Input
					id="password"
					type="password"
					autocomplete="new-password"
					bind:value={password}
					aria-invalid={!!errors.password}
					aria-describedby={errors.password ? 'password-err' : undefined}
					disabled={loading}
					placeholder="••••••••"
					class={invalidClasses}
				/>
				{#if errors.password}
					<span class={errorClasses} id="password-err" aria-live="polite">{errors.password}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="confirm" class={labelClasses}>Confirm Password</label>
				<Input
					id="confirm"
					type="password"
					autocomplete="new-password"
					bind:value={confirmPassword}
					aria-invalid={!!errors.confirmPassword}
					aria-describedby={errors.confirmPassword ? 'confirm-err' : undefined}
					disabled={loading}
					placeholder="••••••••"
					class={invalidClasses}
				/>
				{#if errors.confirmPassword}
					<span class={errorClasses} id="confirm-err" aria-live="polite"
						>{errors.confirmPassword}</span
					>
				{/if}
			</div>

			<Button type="submit" variant="primary" disabled={loading} class="mt-2 w-full">
				{loading ? 'Registering...' : 'Register'}
			</Button>
		</form>

		<p class="mt-8 text-center text-sm text-muted">
			Already have an account?
			<a href={resolve('/account/login')} class="font-bold text-primary underline">Log in</a>
		</p>
	</main>
</div>
