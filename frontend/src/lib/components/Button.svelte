<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'default' | 'primary' | 'accent' | 'danger';

	let {
		variant = 'default',
		href = undefined,
		type = 'button',
		disabled = false,
		class: className = '',
		children,
		...rest
	}: {
		variant?: Variant;
		href?: string;
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		class?: string;
		children: Snippet;
		[key: string]: unknown;
	} = $props();

	const base =
		'inline-flex cursor-pointer items-center justify-center gap-2 border-4 border-ink px-6 py-3 font-display text-base leading-none font-bold no-underline shadow-nb-sm transition-[translate,box-shadow,background-color] duration-[120ms] ease-out hover:not-disabled:-translate-x-0.5 hover:not-disabled:-translate-y-0.5 hover:not-disabled:shadow-nb focus-visible:-translate-x-0.5 focus-visible:-translate-y-0.5 focus-visible:shadow-nb active:not-disabled:translate-x-[3px] active:not-disabled:translate-y-[3px] active:not-disabled:shadow-none disabled:cursor-not-allowed disabled:bg-bg-alt disabled:text-muted disabled:opacity-60 disabled:shadow-none';

	const variants: Record<Variant, string> = {
		default: 'bg-bg text-ink',
		primary: 'bg-primary text-on-primary',
		accent: 'bg-accent text-ink',
		danger: 'bg-danger text-on-danger'
	};

	const classes = $derived(`${base} ${variants[variant]} ${className}`);
</script>

{#if href}
	<a {href} class={classes} {...rest}>{@render children()}</a>
{:else}
	<button {type} {disabled} class={classes} {...rest}>{@render children()}</button>
{/if}
