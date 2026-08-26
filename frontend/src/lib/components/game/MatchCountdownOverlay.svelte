<script lang="ts">
	type Props = {
		value: number;
		players: string[];
		me: string;
		word: string;
		isRanked: boolean;
		myElo: number | null;
		opponentElo: number | null;
	};

	let { value, players, me, word, isRanked, myElo, opponentElo }: Props = $props();

	function isMe(player: string): boolean {
		return player === me;
	}

	function playerLabel(player: string): string {
		return isMe(player) ? 'You' : player;
	}

	function playerElo(player: string): number | null {
		return isMe(player) ? myElo : opponentElo;
	}

	function countdownColors(): string {
		if (value >= 5) return 'bg-primary text-on-primary';
		if (value === 4) return 'bg-highlight text-on-primary';
		if (value === 3) return 'bg-accent text-ink';
		if (value === 2) return 'bg-bg-alt text-ink';
		return 'bg-danger text-on-danger';
	}
</script>

<div
	class="fixed inset-0 z-[900] grid grid-rows-[32vh_1fr_16vh] overflow-hidden bg-bg sm:grid-rows-[28vh_1fr_18vh]"
	role="dialog"
	aria-modal="true"
	aria-label={`Game starts in ${value}`}
>
	<div class="flex flex-wrap border-b-4 border-ink">
		{#each players as player, index (player)}
			<div
				class="flex min-w-[20%] flex-1 animate-cd-half-in flex-col justify-center gap-2 p-4 sm:px-12 sm:py-6 {isMe(
					player
				)
					? ''
					: 'items-end text-right [animation-delay:0.06s]'}"
			>
				<span class="font-mono text-xs font-bold tracking-[0.22em] text-muted uppercase">
					Player {String(index + 1).padStart(2, '0')}
				</span>
				<span
					class="max-w-[42vw] overflow-hidden font-display text-[clamp(1.1rem,5.5vw,2rem)] leading-none font-extrabold text-ellipsis whitespace-nowrap uppercase sm:text-[clamp(1.6rem,4.5vw,3.5rem)] {isMe(
						player
					)
						? 'text-primary'
						: 'text-danger'}"
				>
					{playerLabel(player)}
				</span>
				{#if isRanked}
					<span class="font-mono text-2xl font-bold text-ink">
						{playerElo(player) ?? '-'}<em
							class="ml-1 text-xs font-normal tracking-[0.12em] text-muted not-italic">ELO</em
						>
					</span>
				{/if}
			</div>
		{/each}
	</div>

	<div class="flex items-center justify-center border-b-4 border-ink {countdownColors()}">
		{#key value}
			<div
				class="pointer-events-none animate-cd-num-stamp font-display text-[min(42vh,54vw)] leading-none font-extrabold select-none sm:text-[min(48vh,40vw)]"
				aria-live="assertive"
				aria-atomic="true"
			>
				{value}
			</div>
		{/key}
	</div>

	<div class="flex animate-cd-bot-in items-center justify-center bg-ink px-8">
		<span
			class="font-display text-[clamp(1.4rem,7vw,2.2rem)] font-extrabold tracking-[0.03em] text-accent uppercase sm:text-[clamp(2rem,5vw,4rem)]"
		>
			{word}
		</span>
	</div>
</div>
