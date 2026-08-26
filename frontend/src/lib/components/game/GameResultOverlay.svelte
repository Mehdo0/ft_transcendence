<script lang="ts">
	import Button from '$lib/components/Button.svelte';

	type GameResult = 'winner' | 'loser' | 'draw';

	type Props = {
		result: GameResult;
		isRanked: boolean;
		eloDiff: number;
		reason: string | null;
		actionLabel: string;
		onaction: () => void;
	};

	let { result, isRanked, eloDiff, reason, actionLabel, onaction }: Props = $props();

	function panelClasses(): string {
		if (result === 'winner') return 'bg-success';
		if (result === 'loser') return 'bg-danger text-on-danger';
		return 'bg-accent';
	}

	function title(): string {
		if (result === 'winner') return 'You Won!';
		if (result === 'loser') return 'You Lost';
		return 'Draw';
	}

	function eloLabel(): string {
		if (!isRanked || result === 'draw') return 'No Elo change';
		return `${eloDiff > 0 ? '+' : ''}${eloDiff} Elo`;
	}
</script>

<div
	class="fixed inset-0 z-[1000] flex items-center justify-center bg-scrim"
	role="dialog"
	aria-modal="true"
>
	<div
		class="m-4 animate-pop-in border-4 border-ink px-6 py-8 text-center shadow-nb-lg md:px-16 md:py-12 {panelClasses()}"
	>
		<h2 class="text-5xl uppercase">{title()}</h2>
		<div class="mt-3 mb-8 flex flex-col items-center gap-3">
			<p class="font-mono text-xl font-bold">{eloLabel()}</p>
			{#if result === 'winner' && reason}
				<p
					class="border-4 border-ink bg-bg px-4 py-3 font-mono text-sm font-bold text-ink shadow-nb-sm"
				>
					{reason}
				</p>
			{/if}
		</div>
		<Button variant="primary" onclick={onaction}>{actionLabel}</Button>
	</div>
</div>
