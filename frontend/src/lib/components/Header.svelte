<script lang="ts">
	import { page } from '$app/stores';
	import favicon from '$lib/draw_meter_logo.svg';
	import Button from '$lib/components/Button.svelte';

	let {
		login = false,
		menuOpen = false,
		navLinks,
		toggleMenu,
		onLogout
	}: {
		login?: boolean;
		menuOpen?: boolean;
		navLinks: { href: string; label: string }[];
		toggleMenu: () => void;
		onLogout: () => void;
	} = $props();

	const linkBase =
		"relative inline-block w-full py-1 font-display text-xs font-bold tracking-[0.02em] whitespace-nowrap text-ink uppercase no-underline transition-colors duration-[120ms] after:absolute after:bottom-0 after:left-0 after:h-[3px] after:w-full after:origin-left after:transition-[scale] after:duration-[120ms] after:content-[''] nav:w-auto";
</script>

<header class="sticky top-0 z-100 border-b-4 border-ink bg-bg">
	<div
		class="relative mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-6 py-3 nav:gap-6"
	>
		<a href="/" class="flex items-center gap-3 font-semibold text-ink no-underline">
			<span
				class="inline-flex shrink-0 items-center justify-center border-4 border-ink bg-accent p-1 shadow-nb-sm"
			>
				<img src={favicon} alt="" class="block h-7 w-auto" />
			</span>
			<span
				class="font-display text-xl font-extrabold tracking-[-0.02em] whitespace-nowrap uppercase"
			>
				Draw Meter
			</span>
		</a>

		<button
			class="flex h-11 w-11 cursor-pointer flex-col justify-center gap-[5px] border-4 border-ink bg-bg px-2 shadow-nb-sm transition-[translate,box-shadow] duration-[120ms] ease-out hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-nb active:translate-x-0 active:translate-y-0 active:shadow-none nav:hidden"
			aria-label="Menu"
			aria-expanded={menuOpen}
			aria-controls="nav-mobile"
			onclick={toggleMenu}
		>
			<span
				class="block h-[3px] w-full bg-ink transition-[translate,rotate,opacity] duration-[120ms] ease-out {menuOpen
					? 'translate-y-[8px] rotate-45'
					: ''}"
			></span>
			<span
				class="block h-[3px] w-full bg-ink transition-[translate,rotate,opacity] duration-[120ms] ease-out {menuOpen
					? 'opacity-0'
					: ''}"
			></span>
			<span
				class="block h-[3px] w-full bg-ink transition-[translate,rotate,opacity] duration-[120ms] ease-out {menuOpen
					? '-translate-y-[8px] -rotate-45'
					: ''}"
			></span>
		</button>

		<div
			id="nav-mobile"
			class="absolute top-full right-0 left-0 z-100 flex-col gap-4 border-b-4 border-ink bg-bg px-6 pt-4 pb-6 shadow-nb nav:static nav:contents nav:animate-none {menuOpen
				? 'flex animate-drawer-in'
				: 'hidden'}"
		>
			<nav class="w-full nav:w-auto" aria-label="Main navigation">
				<ul class="flex list-none flex-col gap-2 p-0 nav:flex-row nav:gap-6">
					{#each navLinks as link (link.href)}
						{@const isActive = $page.url.pathname === link.href}
						<li>
							<a
								href={link.href}
								class="{linkBase} {isActive
									? 'after:scale-x-100 after:bg-ink'
									: 'after:scale-x-0 after:bg-accent hover:after:scale-x-100 focus-visible:after:scale-x-100'}"
								aria-current={isActive ? 'page' : undefined}
							>
								{link.label}
							</a>
						</li>
					{/each}
				</ul>
			</nav>

			<div
				class="flex w-full flex-col items-stretch gap-3 border-t-4 border-ink pt-4 nav:w-auto nav:flex-row nav:items-center nav:border-t-0 nav:pt-0"
			>
				{#if !login}
					<Button href="/account/login" class="w-full nav:w-auto">Login</Button>
					<Button href="/account/register" variant="primary" class="w-full nav:w-auto">
						Register
					</Button>
				{:else}
					<Button variant="danger" onclick={onLogout} class="w-full nav:w-auto">Logout</Button>
				{/if}
			</div>
		</div>
	</div>
</header>
