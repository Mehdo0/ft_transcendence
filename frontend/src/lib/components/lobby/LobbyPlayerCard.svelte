<script lang="ts">
	type Props = {
		username: string;
		isHost: boolean;
	};

	let { username, isHost }: Props = $props();

	function monogram(): string {
		const normalized = username.trim();
		if (normalized.length <= 1) return normalized.toUpperCase();
		return `${normalized[0]}${normalized.at(-1)}`.toUpperCase();
	}
</script>

<div class="flex min-w-0 flex-col items-center gap-3 text-center" title={username}>
	<div
		class="flex h-20 w-20 items-center justify-center border-4 border-ink font-display text-2xl font-extrabold shadow-nb-sm {isHost
			? 'bg-accent text-ink'
			: 'bg-primary text-on-primary'}"
		aria-hidden="true"
	>
		{monogram()}
	</div>

	<div class="flex min-h-12 w-full min-w-0 flex-col items-center gap-1">
		<span class="max-w-full font-mono text-xs leading-tight font-bold break-all text-ink">
			{username}
		</span>
		{#if isHost}
			<span
				class="border-2 border-ink bg-accent px-2 py-0.5 font-mono text-[10px] leading-none font-bold tracking-[0.08em] text-ink uppercase"
			>
				Host
			</span>
		{/if}
	</div>
</div>
