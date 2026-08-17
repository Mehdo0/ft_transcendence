<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		class: className = '',
		children
	}: {
		class?: string;
		children: Snippet;
	} = $props();
</script>

<div
	class="border-4 border-ink bg-danger px-4 py-3 text-sm font-bold text-on-danger shadow-nb-sm {className}"
	role="alert"
>
	{@render children()}
</div>
