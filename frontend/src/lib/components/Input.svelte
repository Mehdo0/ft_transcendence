<script lang="ts">
	let {
		value = $bindable(''),
		mono = false,
		class: className = '',
		...rest
	}: {
		value?: string;
		mono?: boolean;
		class?: string;
		[key: string]: unknown;
	} = $props();

	const base =
		'w-full border-4 border-ink bg-bg px-4 py-3 font-sans text-base text-ink shadow-nb-sm transition-[translate,box-shadow] duration-[120ms] ease-out placeholder:text-muted hover:not-disabled:-translate-x-0.5 hover:not-disabled:-translate-y-0.5 hover:not-disabled:shadow-nb focus-visible:-translate-x-0.5 focus-visible:-translate-y-0.5 focus-visible:shadow-nb focus-visible:outline-none disabled:cursor-not-allowed disabled:bg-bg-alt disabled:text-muted disabled:opacity-60 disabled:shadow-none';

	const monoClasses = 'font-mono font-bold tracking-[0.15em] uppercase';
</script>

<input bind:value class="{base} {mono ? monoClasses : ''} {className}" {...rest} />
