<script lang="ts">
	let {
		title,
		subtitle = '',
		size = 'md',
		class: className = ''
	}: {
		title: string;
		subtitle?: string;
		size?: 'md' | 'lg';
		class?: string;
	} = $props();

	const sizes = { md: 'text-3xl', lg: 'text-5xl' };
</script>

<div class={className}>
	<h1 class="mb-1 uppercase {sizes[size]}">{title}</h1>
	{#if subtitle}
		<p class="text-muted">{subtitle}</p>
	{/if}
</div>
