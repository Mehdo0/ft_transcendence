<script lang="ts">
	import { onMount } from 'svelte';
	import ErrorBox from '$lib/components/ErrorBox.svelte';

	type Player = { username: string; elo: number };

	let players = $state<Player[]>([]);
	let me = $state('');
	let errorMessage = $state('');

	const rowBase = 'flex items-center gap-3 border-4 bg-bg p-3';
	const rankBase =
		'flex h-9 w-9 flex-shrink-0 items-center justify-center border-4 border-ink font-display text-base font-extrabold';

	function rowClasses(index: number, username: string) {
		const isMe = me && username === me;
		return [
			rowBase,
			index < 3 ? 'shadow-nb-sm' : '',
			isMe ? 'border-primary shadow-nb-accent' : 'border-ink'
		].join(' ');
	}

	function rankClasses(index: number) {
		if (index === 0) return `${rankBase} bg-accent text-ink`;
		if (index === 1) return `${rankBase} bg-silver text-ink`;
		if (index === 2) return `${rankBase} bg-highlight text-on-primary`;
		return `${rankBase} bg-bg-alt text-muted`;
	}

	onMount(async () => {
		try {
			const meRes = await fetch('/api/session/', { credentials: 'same-origin' });
			const session = await meRes.json();
			if (session.authenticated && session.user) {
				me = session.user.username;
			}
		} catch {
			// not logged in — no highlighting
		}

		try {
			const res = await fetch('/api/get_ranking');

			if (res.ok) {
				players = await res.json();
			} else {
				errorMessage = 'Failed to load leaderboard.';
			}
		} catch {
			errorMessage = 'Could not connect to the server.';
		}
	});
</script>

<svelte:head>
	<title>Leaderboard — Draw Meter</title>
</svelte:head>

<div class="flex flex-1 items-start justify-center py-8">
	<div class="w-full max-w-[480px] border-4 border-ink bg-bg p-6 shadow-nb-lg">
		<header class="mb-6 text-center">
			<h1 class="mb-1 text-3xl uppercase">Leaderboard</h1>
			<p class="font-mono text-sm tracking-[0.1em] text-muted uppercase">Top 10 Players</p>
		</header>

		{#if errorMessage}
			<ErrorBox class="mb-6 text-center">{errorMessage}</ErrorBox>
		{/if}

		<ol class="flex list-none flex-col gap-2 p-0">
			{#each players as player, index (player.username)}
				<li class={rowClasses(index, player.username)}>
					<span class={rankClasses(index)}>{index + 1}</span>
					<span
						class="flex min-w-0 grow items-center gap-2 overflow-hidden font-display text-xl font-bold text-ellipsis whitespace-nowrap"
					>
						{player.username}
						{#if me && player.username === me}
							<span
								class="flex-shrink-0 border-2 border-ink bg-primary px-2 font-mono text-xs font-bold tracking-[0.05em] text-on-primary uppercase"
							>
								You
							</span>
						{/if}
					</span>
					<span class="flex-shrink-0 font-mono text-xl font-bold tabular-nums">{player.elo}</span>
				</li>
			{/each}

			{#if players.length === 0 && !errorMessage}
				<li class="p-6 text-center text-muted italic">No players ranked yet.</li>
			{/if}
		</ol>
	</div>
</div>
