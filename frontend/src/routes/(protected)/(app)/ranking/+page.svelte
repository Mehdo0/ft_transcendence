<script lang="ts">
	import { onMount } from 'svelte';
	import ErrorBox from '$lib/components/ErrorBox.svelte';
	import { getSession } from '$lib/session';

	type Player = { rank: number; username: string; elo: number };
	type RankingResponse = {
		players: Player[];
		current: Player | null;
		limit: number;
	};

	let players = $state<Player[]>([]);
	let currentPlayer = $state<Player | null>(null);
	let rankingLimit = $state(0);
	let me = $state('');
	let isGuest = $state(false);
	let errorMessage = $state('');

	const rowBase = 'flex items-center gap-3 border-4 bg-bg p-3';
	const rankBase =
		'flex h-9 w-9 flex-shrink-0 items-center justify-center border-4 border-ink font-display text-base font-extrabold';

	function rowClasses(rank: number, username: string) {
		const isMe = me && username === me;
		return [
			rowBase,
			rank <= 3 ? 'shadow-nb-sm' : '',
			isMe ? 'border-primary shadow-nb-accent' : 'border-ink'
		].join(' ');
	}

	function rankClasses(rank: number) {
		if (rank === 1) return `${rankBase} bg-accent text-ink`;
		if (rank === 2) return `${rankBase} bg-silver text-ink`;
		if (rank === 3) return `${rankBase} bg-highlight text-on-primary`;
		return `${rankBase} bg-bg-alt text-muted`;
	}

	onMount(async () => {
		try {
			const session = await getSession();
			if (session.authenticated) {
				me = session.user.username;
				isGuest = session.user.is_guest;
			}
		} catch {
			me = '';
			isGuest = false;
		}

		try {
			const res = await fetch('/api/get_ranking', { credentials: 'same-origin' });

			if (res.ok) {
				const ranking = (await res.json()) as RankingResponse;
				players = ranking.players;
				currentPlayer = ranking.current;
				rankingLimit = ranking.limit;
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
			<p class="font-mono text-sm tracking-[0.1em] text-muted uppercase">
				{rankingLimit > 0 ? `Top ${rankingLimit} Players` : 'Top Players'}
			</p>
		</header>

		{#if errorMessage}
			<ErrorBox class="mb-6 text-center">{errorMessage}</ErrorBox>
		{/if}

		<ol class="flex list-none flex-col gap-2 p-0">
			{#each players as player (player.username)}
				<li class={rowClasses(player.rank, player.username)}>
					<span class={rankClasses(player.rank)}>{player.rank}</span>
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

		{#if currentPlayer && currentPlayer.rank > rankingLimit}
			<div class="mt-8 border-t-4 border-dashed border-ink pt-5">
				<p
					class="mb-3 text-center font-mono text-xs font-bold tracking-[0.16em] text-muted uppercase"
				>
					Your Position
				</p>
				<div class={rowClasses(currentPlayer.rank, currentPlayer.username)}>
					<span class={rankClasses(currentPlayer.rank)}>{currentPlayer.rank}</span>
					<span
						class="flex min-w-0 grow items-center gap-2 overflow-hidden font-display text-xl font-bold text-ellipsis whitespace-nowrap"
					>
						{currentPlayer.username}
						<span
							class="flex-shrink-0 border-2 border-ink bg-primary px-2 font-mono text-xs font-bold tracking-[0.05em] text-on-primary uppercase"
						>
							You
						</span>
					</span>
					<span class="flex-shrink-0 font-mono text-xl font-bold tabular-nums">
						{currentPlayer.elo}
					</span>
				</div>
			</div>
		{:else if isGuest}
			<p class="mt-8 border-t-4 border-dashed border-ink pt-5 text-center text-sm text-muted">
				Guest players are unranked.
			</p>
		{/if}
	</div>
</div>
