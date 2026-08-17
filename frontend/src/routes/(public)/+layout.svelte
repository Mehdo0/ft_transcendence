<script lang="ts">
	import { page } from '$app/stores';
	import favicon from '$lib/draw_meter_logo.svg';
	import { onMount } from 'svelte';
	import Footer from '$lib/components/Footer.svelte';
	import Header from '$lib/components/Header.svelte';

	let { children } = $props();
	let login = $state(false);
	let menuOpen = $state(false);

	const navLinks = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/start_game', label: 'Play Now!' },
		{ href: '/lobby', label: 'Private Game' },
		{ href: '/ranking', label: 'Leaderboard' }
	];

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

	

	onMount(async () => {
		const response = await fetch('/api/session/', {
			method: 'GET',
			credentials: 'same-origin'
		});
		const session = await response.json();

		if (session.authenticated) {
			login = true;
			return;
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Draw Meter</title>
</svelte:head>

<div class="flex min-h-screen flex-col">
	<Header {login} {menuOpen} {navLinks} {toggleMenu} onLogout={handleLogout} />

	<main class="mx-auto flex w-full max-w-[1200px] grow flex-col px-4 py-6 nav:p-8">
		{@render children()}
	</main>

	<Footer />
</div>
