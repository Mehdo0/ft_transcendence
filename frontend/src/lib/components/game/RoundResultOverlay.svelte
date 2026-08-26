<script lang="ts">
	import DrawingReplay from './DrawingReplay.svelte';
	import type { RoundResult } from '$lib/game/roundResult';

	let {
		result,
		players,
		me
	}: {
		result: RoundResult;
		players: string[];
		me: string;
	} = $props();

	let remaining = $state(0);
	let elapsed = $state(0);
	let liveScores = $state<Record<string, number>>({});
	let replayPlayers = $derived(players.length > 0 ? players : Object.keys(result.scores));
	let playbackDuration = $derived(Math.max(0.1, result.duration - result.final_hold_duration));
	let showFinalResult = $derived(elapsed >= playbackDuration);

	function playerLabel(username: string): string {
		return username === me ? 'You' : username;
	}

	function scoreBarClasses(username: string): string {
		if (username === me) {
			return 'bg-[repeating-linear-gradient(45deg,var(--color-primary)_0_14px,var(--color-primary-dark)_14px_28px)]';
		}
		return 'bg-[repeating-linear-gradient(45deg,var(--color-danger)_0_14px,var(--color-danger-dark)_14px_28px)]';
	}

	function title(): string {
		if (result.is_tie || !result.winner) return 'Round Draw';
		if (result.winner === me) return 'You Won The Round!';
		return `${result.winner} Wins The Round!`;
	}

	function cardLayout(index: number): string {
		if (replayPlayers.length === 3 && index === 2) {
			return 'col-span-2 mx-auto w-1/2';
		}
		return '';
	}

	function score(username: string): number {
		return Math.max(0, Math.min(100, liveScores[username] ?? 0));
	}

	function updateScore(username: string, value: number): void {
		liveScores = { ...liveScores, [username]: value };
	}

	$effect(() => {
		const startedAt = Date.now();
		remaining = Math.ceil(result.duration);
		const timer = window.setInterval(() => {
			elapsed = (Date.now() - startedAt) / 1000;
			remaining = Math.max(0, Math.ceil(result.duration - elapsed));
		}, 100);

		return () => window.clearInterval(timer);
	});
</script>

<div
	class="fixed inset-0 z-[950] overflow-y-auto bg-bg p-3 sm:p-6"
	role="dialog"
	aria-modal="true"
	aria-label="Round result"
>
	<section class="mx-auto flex min-h-full w-full max-w-[960px] flex-col justify-center gap-4">
		<header class="border-4 border-ink bg-accent px-4 py-3 text-center shadow-nb sm:px-8">
			<p class="font-mono text-xs font-bold tracking-[0.2em] text-muted uppercase">
				Round {result.round_number}
			</p>
			<h2 class="mt-1 text-2xl uppercase sm:text-4xl">
				{showFinalResult ? title() : 'Replay'}
			</h2>
		</header>

		<div class="grid grid-cols-2 gap-3 sm:gap-4">
			{#each replayPlayers as player, index (player)}
				<article
					class="border-4 border-ink p-2 shadow-nb-sm sm:p-3 {showFinalResult &&
					result.winner === player
						? 'bg-success'
						: 'bg-bg-alt'} {cardLayout(index)}"
				>
					<div class="mb-2 flex items-center justify-between gap-2">
						<h3 class="truncate text-xs uppercase sm:text-base">{playerLabel(player)}</h3>
						{#if showFinalResult && result.winner === player}
							<span
								class="border-2 border-ink bg-accent px-2 py-1 font-mono text-[10px] font-bold uppercase"
							>
								Winner
							</span>
						{/if}
					</div>

					<div class="mx-auto w-full max-w-[210px]">
						<DrawingReplay
							events={result.timelines[player] ?? []}
							{playbackDuration}
							timelineDuration={result.timeline_duration}
							onscorechange={(value) => updateScore(player, value)}
						/>
					</div>

					<div class="mt-2 flex items-center gap-2">
						<div class="h-4 flex-1 overflow-hidden border-2 border-ink bg-bg">
							<div class="h-full {scoreBarClasses(player)}" style="width: {score(player)}%"></div>
						</div>
						<strong class="font-mono text-sm tabular-nums">{Math.round(score(player))}%</strong>
					</div>
				</article>
			{/each}
		</div>

		<footer class="border-4 border-ink bg-ink px-4 py-3 text-center text-white shadow-nb-sm">
			<p class="font-mono text-xs font-bold tracking-[0.12em] uppercase">
				{result.match_complete ? 'Match result' : 'Next round'} in {remaining}s
			</p>
		</footer>
	</section>
</div>
