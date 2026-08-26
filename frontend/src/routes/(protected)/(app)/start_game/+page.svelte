<script lang="ts">
	import { onMount } from 'svelte';
	import { goto, beforeNavigate } from '$app/navigation';
	import { resolve } from '$app/paths';
	import {
		connect,
		send,
		subscribe,
		subscribeConnection,
		type ConnectionStatus
	} from '$lib/stores/wsManager';
	import { game } from '$lib/stores/game.svelte';
	import Button from '$lib/components/Button.svelte';
	import { saveRoundTiming } from '$lib/game/roundTiming';
	import type { MatchFoundMessage } from '$lib/websocket/serverMessage';

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
		if (confirm('Cancel matchmaking?')) {
			cancelMatchmaking();
		} else {
			nav.cancel();
		}
	});

	function handleMatchFound(msg: MatchFoundMessage) {
		isSearching = false;
		statusMessage = 'Game found';
		game.id = msg.game_id;
		game.opponents = msg.opponent ?? [];
		game.players = msg.players ?? [];
		game.me = msg.me ?? '';
		game.word = msg.word;
		game.scores = {};
		game.round_number = msg.round_number ?? 1;
		game.is_ranked = msg.is_ranked ?? true;
		sessionStorage.removeItem('private_lobby_code');
		sessionStorage.removeItem('draw_in_progress');
		saveRoundTiming(msg.duration + msg.countdown, msg.countdown);
		leaving = true;
		goto(resolve('/in-game'));
	}

	function findGame() {
		send({ type: 'find_player' });
		isSearching = true;
		statusMessage = 'Searching...';
	}

	function cancelMatchmaking() {
		if (!isSearching) return;
		send({ type: 'cancel_matchmaking' });
		isSearching = false;
		statusMessage = 'Connected';
	}

	function handleConnectionStatus(status: ConnectionStatus) {
		isConnected = status === 'connected';
		if (isSearching && status !== 'connected') isSearching = false;
		if (isSearching) return;

		if (status === 'connected') statusMessage = 'Connected';
		else if (status === 'connecting') statusMessage = 'Connecting';
		else statusMessage = 'Disconnected';
	}

	onMount(() => {
		const unsubscribeMessages = subscribe((message) => {
			if (message.type === 'match_found') {
				handleMatchFound(message);
			}
			if (message.type === 'waiting') {
				isSearching = true;
				statusMessage = 'Searching...';
			}
			if (message.type === 'matchmaking_cancelled') {
				isSearching = false;
				statusMessage = 'Connected';
			}
		});
		const unsubscribeConnection = subscribeConnection(handleConnectionStatus);

		void connect().catch(() => undefined);

		return () => {
			unsubscribeMessages();
			unsubscribeConnection();
		};
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
			aria-live="polite"
		>
			<span class="h-3 w-3 border-2 border-ink {dotClasses}"></span>
			<span>{statusMessage}</span>
		</div>

		{#if isSearching}
			<button
				class="cursor-pointer border-b-2 border-transparent px-2 py-1 font-mono text-sm font-bold text-muted transition-colors hover:border-danger hover:text-danger focus-visible:border-danger focus-visible:text-danger focus-visible:outline-none"
				onclick={cancelMatchmaking}
			>
				Leave queue
			</button>
		{:else}
			<Button
				variant="primary"
				onclick={findGame}
				disabled={!isConnected}
				class="h-14 w-full text-xl"
			>
				Find Game
			</Button>
		{/if}
	</div>
</div>
