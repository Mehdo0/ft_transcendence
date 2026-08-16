<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		updated,
		children
	}: {
		title: string;
		updated: string;
		children: Snippet;
	} = $props();
</script>

<div class="flex flex-1 justify-center py-8">
	<article class="w-full max-w-[760px] border-4 border-ink bg-bg p-6 shadow-nb-lg">
		<header class="mb-6 border-b-4 border-ink pb-4">
			<h1 class="mb-2 text-5xl uppercase">{title}</h1>
			<p class="font-mono text-sm text-muted">Last updated: {updated}</p>
		</header>

		{@render children()}
	</article>
</div>
