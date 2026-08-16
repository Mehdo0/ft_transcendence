<script lang="ts">
	import { login } from '$lib/api';
	import Button from '$lib/components/Button.svelte';
	import ErrorBox from '$lib/components/ErrorBox.svelte';
	import Input from '$lib/components/Input.svelte';
	import PageTitle from '$lib/components/PageTitle.svelte';

	let username = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleLogin(event: Event) {
		event.preventDefault();

		errorMessage = '';
		isLoading = true;

		try {
			const result = await login(username, password);
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

<div class="flex flex-1 items-center justify-center py-8">
	<main class="w-full max-w-[420px] border-4 border-ink bg-bg p-6 shadow-nb-lg">
		<PageTitle title="Welcome Back" subtitle="Log in to play" class="mb-8" />

		{#if errorMessage}
			<ErrorBox class="mb-6">{errorMessage}</ErrorBox>
		{/if}

		<form onsubmit={handleLogin} class="flex flex-col gap-6">
			<div class="flex flex-col gap-2 text-left">
				<label for="username" class="font-display text-sm font-bold tracking-[0.02em] uppercase"
					>Username</label
				>
				<Input
					type="text"
					id="username"
					autocomplete="username"
					bind:value={username}
					required
					disabled={isLoading}
				/>
			</div>

			<div class="flex flex-col gap-2 text-left">
				<label for="password" class="font-display text-sm font-bold tracking-[0.02em] uppercase"
					>Password</label
				>
				<Input
					type="password"
					id="password"
					autocomplete="current-password"
					bind:value={password}
					required
					disabled={isLoading}
				/>
			</div>

			<Button type="submit" variant="primary" disabled={isLoading} class="mt-2 w-full">
				{isLoading ? 'Logging in...' : 'Log In'}
			</Button>
		</form>

		<p class="mt-8 text-center text-sm text-muted">
			Don't have an account?
			<a href="/account/register" class="font-bold text-primary underline">Register here</a>
		</p>
	</main>
</div>
