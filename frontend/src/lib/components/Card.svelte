<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		interactive = false,
		class: className = '',
		children,
		...rest
	}: {
		interactive?: boolean;
		class?: string;
		children: Snippet;
		[key: string]: unknown;
	} = $props();

	const base = 'border-4 border-ink bg-bg p-6 shadow-nb';
	const interactiveClasses =
		'transition-[translate,box-shadow] duration-[120ms] ease-out hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-nb active:translate-x-[3px] active:translate-y-[3px] active:shadow-none';
</script>

<div class="{base} {interactive ? interactiveClasses : ''} {className}" {...rest}>
	{@render children()}
</div>
