<script lang="ts">
	import { page } from '$app/stores';
	import favicon from '$lib/draw_meter_logo.svg';
	import { onMount } from 'svelte';

	let { children } = $props();

	let login = $state(false);
	let menuOpen = $state(false);

	function toggleMenu() {
		menuOpen = !menuOpen;
	}

	function closeMenu() {
		menuOpen = false;
	}

	$effect(() => {
		$page.url.pathname;
		menuOpen = false;
	});

	async function handleLogout() {
		closeMenu();
		await fetch('/api/logout', {
			method: 'POST',
			credentials: 'same-origin'
		});
		location.assign('/');
	}

	const navLinks = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/start_game', label: 'Play Now!' },
		{ href: '/lobby', label: 'Private Game' },
		{ href: '/ranking', label: 'Leaderboard' }
	];

	onMount(async () => {
		const response = await fetch('/api/session/', {
			method: 'GET',
			credentials: 'same-origin'
		});
		const session = await response.json();
		if (session.authenticated) {
			login = true;
		}

	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Draw Meter</title>
</svelte:head>

<div class="app-layout">
	<header class="navbar">
		<div class="nav-container">
			<a href="/" class="nav-brand">
				<span class="nav-logo-box">
					<img src={favicon} alt="" class="nav-logo" />
				</span>
				<span class="nav-title">Draw Meter</span>
			</a>

			<button
				class="nav-burger"
				class:open={menuOpen}
				aria-label="Menu"
				aria-expanded={menuOpen}
				aria-controls="nav-mobile"
				onclick={toggleMenu}
			>
				<span></span>
				<span></span>
				<span></span>
			</button>

			<div class="nav-drawer" id="nav-mobile" class:open={menuOpen}>
				<nav class="nav-menu" aria-label="Main navigation">
					<ul>
						{#each navLinks as link (link.href)}
							<li>
								<a
									href={link.href}
									class="nav-link"
									class:active={$page.url.pathname === link.href}
									aria-current={$page.url.pathname === link.href ? 'page' : undefined}
								>
									{link.label}
								</a>
							</li>
						{/each}
					</ul>
				</nav>

				<div class="nav-actions">
					{#if !login}
						<a href="/account/login" class="nb-btn">Login</a>
						<a href="/account/register" class="nb-btn nb-btn--primary">Register</a>
					{:else}
						<button class="nb-btn nb-btn--danger" onclick={handleLogout}>Logout</button>
					{/if}
				</div>
			</div>
		</div>
	</header>

	<main class="content-wrapper">
		{@render children()}
	</main>

	<footer class="site-footer">
		<div class="footer-container">
			<span class="footer-brand">DRAW METER</span>
			<nav class="footer-links" aria-label="Legal links">
				<a href="/privacy">Privacy Policy</a>
				<a href="/terms">Terms of Service</a>
			</nav>
			<span class="footer-copy">© 2026 — 42 Lausanne</span>
		</div>
	</footer>
</div>

<style>
	.app-layout {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.navbar {
		background: var(--c-bg);
		border-bottom: var(--border-lg);
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.nav-container {
		position: relative;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--space-5);
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--space-3) var(--space-6);
	}

	.nav-drawer {
		display: contents;
	}

	.nav-burger {
		display: none;
		flex-direction: column;
		justify-content: center;
		gap: 5px;
		width: 44px;
		height: 44px;
		padding: 0 var(--space-2);
		background: var(--c-bg);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		cursor: pointer;
		transition:
			transform var(--transition),
			box-shadow var(--transition);
	}

	.nav-burger:hover {
		transform: translate(calc(-1 * var(--nudge)), calc(-1 * var(--nudge)));
		box-shadow: var(--shadow);
	}

	.nav-burger:active {
		transform: translate(0, 0);
		box-shadow: none;
	}

	.nav-burger span {
		display: block;
		height: var(--border-w);
		width: 100%;
		background: var(--c-ink);
		transition:
			transform var(--transition),
			opacity var(--transition);
	}

	.nav-burger.open span:nth-child(1) {
		transform: translateY(8px) rotate(45deg);
	}

	.nav-burger.open span:nth-child(2) {
		opacity: 0;
	}

	.nav-burger.open span:nth-child(3) {
		transform: translateY(-8px) rotate(-45deg);
	}

	.nav-brand {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		text-decoration: none;
		color: var(--c-ink);
		font-weight: var(--fw-medium);
	}

	.nav-logo-box {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-1);
		background: var(--c-accent);
		border: var(--border);
		box-shadow: var(--shadow-sm);
	}

	.nav-logo {
		height: 28px;
		width: auto;
		display: block;
	}

	.nav-title {
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: var(--fs-lg);
		letter-spacing: -0.02em;
		text-transform: uppercase;
	}

	.nav-menu ul {
		display: flex;
		list-style: none;
		gap: var(--space-5);
		margin: 0;
		padding: 0;
	}

	.nav-link {
		position: relative;
		display: inline-block;
		text-decoration: none;
		color: var(--c-ink);
		font-family: var(--font-display);
		font-weight: var(--fw-bold);
		font-size: var(--fs-xs);
		text-transform: uppercase;
		letter-spacing: 0.02em;
		white-space: nowrap;
		padding: var(--space-1) 0;
		transition: color var(--transition);
	}

	.nav-link::after {
		content: '';
		position: absolute;
		left: 0;
		bottom: 0;
		width: 100%;
		height: var(--border-w);
		background: var(--c-accent);
		transform: scaleX(0);
		transform-origin: left;
		transition: transform var(--transition);
	}

	.nav-link:hover::after,
	.nav-link:focus-visible::after {
		transform: scaleX(1);
	}

	.nav-link.active::after {
		background: var(--c-ink);
		transform: scaleX(1);
	}

	.nav-actions {
		display: flex;
		gap: var(--space-3);
		align-items: center;
	}

	.content-wrapper {
		flex-grow: 1;
		display: flex;
		flex-direction: column;
		padding: var(--space-6);
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
	}

	.site-footer {
		background: var(--c-bg-alt);
		border-top: var(--border-lg);
	}

	.footer-container {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--space-5) var(--space-6);
	}

	.footer-brand {
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: var(--fs-sm);
		letter-spacing: 0.05em;
	}

	.footer-links {
		display: flex;
		gap: var(--space-5);
	}

	.footer-links a {
		color: var(--c-ink);
		font-weight: var(--fw-medium);
		text-decoration: none;
		border-bottom: var(--border-w) solid transparent;
		transition: border-color var(--transition);
	}

	.footer-links a:hover {
		border-bottom-color: var(--c-ink);
	}

	.footer-copy {
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		color: var(--c-muted);
	}

	@media (max-width: 900px) {
		.nav-container {
			justify-content: space-between;
			gap: var(--space-3);
		}

		.nav-burger {
			display: flex;
		}

		.nav-drawer {
			display: none;
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			flex-direction: column;
			gap: var(--space-4);
			padding: var(--space-4) var(--space-6) var(--space-5);
			background: var(--c-bg);
			border-bottom: var(--border-lg);
			box-shadow: var(--shadow);
			z-index: 100;
		}

		.nav-drawer.open {
			display: flex;
			animation: drawer-in var(--transition) ease;
		}

		.nav-menu {
			width: 100%;
		}

		.nav-menu ul {
			flex-direction: column;
			gap: var(--space-2);
		}

		.nav-link {
			display: block;
			width: 100%;
		}

		.nav-actions {
			flex-direction: column;
			align-items: stretch;
			width: 100%;
			padding-top: var(--space-4);
			border-top: var(--border-w) solid var(--c-ink);
		}

		.nav-actions :global(.nb-btn) {
			width: 100%;
		}

		.content-wrapper {
			padding: var(--space-5) var(--space-4);
		}

		.footer-container {
			justify-content: center;
			text-align: center;
		}
	}

	@keyframes drawer-in {
		from {
			opacity: 0;
			transform: translateY(-6px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.nav-drawer.open {
			animation: none;
		}
	}
</style>
