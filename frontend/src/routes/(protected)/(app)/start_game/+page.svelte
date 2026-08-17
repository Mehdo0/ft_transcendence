<script lang="ts">
	import { onMount } from 'svelte';
	import { goto, beforeNavigate } from '$app/navigation';
	import { isOpen, send, subscribe, connect } from '$lib/stores/wsManager';
	import { game } from '$lib/stores/game.svelte';
	import Button from '$lib/components/Button.svelte';

	let isConnected = $state(false);
	let isSearching = $state(false);
	let statusMessage = $state('Disconnected');
	let leaving = false;

	const dotClasses = $derived(
		isSearching ? 'animate-blink bg-accent' : isConnected ? 'bg-success' : 'bg-muted'
	);

	beforeNavigate((nav) => {
		if (!isSearching || leaving) return;
		if (nav.willUnload) return;
		if (confirm('Annuler la recherche ?')) {
			send({ type: 'leave' });
		} else {
			nav.cancel();
		}
	});

	function handleMatchFound(msg: any) {
		isSearching = false;
		statusMessage = 'Game found';
		game.id = msg.game_id;
		game.opponents = msg.opponent ?? [];
		game.players = msg.players ?? [];
		game.me = msg.me ?? '';
		game.word = msg.word;
		game.scores = {};
		game.is_ranked = msg.is_ranked ?? true;
		sessionStorage.removeItem('private_lobby_code');
		sessionStorage.removeItem('draw_in_progress');
		sessionStorage.setItem(
			'draw_ends_at',
			String(Date.now() + ((msg.duration ?? 60) + (msg.countdown ?? 0)) * 1000)
		);
		leaving = true;
		goto('/in-game');
	}

	async function findGame() {
		send({ type: 'find_player' });
		isSearching = true;
		statusMessage = 'Searching...';
	}

	onMount(() => {
		const unsubscribe = subscribe((message) => {
			if (message.type === 'match_found') {
				handleMatchFound(message);
			}
		});

		isConnected = isOpen();

		if (isConnected) {
			statusMessage = 'Connected';
		} else {
			statusMessage = 'Connecting';

			connect()
				.then(() => {
					isConnected = true;
					statusMessage = 'Connected';
				})
				.catch(() => {
					isConnected = false;
					statusMessage = 'Disconnected';
				});
		}

		return unsubscribe;
	});
</script>

<svelte:head>
	<title>Matchmaking — Draw Meter</title>
</svelte:head>

<div class="flex flex-1 items-center justify-center py-8">
	<div
		class="flex w-full max-w-[440px] flex-col items-center gap-8 border-4 border-ink bg-bg p-6 shadow-nb-lg"
	>
		<h1 class="text-center text-3xl uppercase">Matchmaking</h1>

		<div
			class="inline-flex items-center gap-3 border-4 border-ink bg-bg-alt px-4 py-2 font-mono text-sm font-bold tracking-[0.05em] uppercase shadow-nb-sm"
		>
			<span class="h-3 w-3 border-2 border-ink {dotClasses}"></span>
			<span>{statusMessage}</span>
		</div>

		<Button
			variant="primary"
			onclick={findGame}
			disabled={!isConnected || isSearching}
			class="h-14 w-full text-xl"
		>
			{isSearching ? 'Searching…' : 'Find Game'}
		</Button>
	</div>
</div>
