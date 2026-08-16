<script lang="ts">
	import { send, subscribe } from '$lib/stores/wsManager';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { game } from '$lib/stores/game.svelte';
	import { goto, beforeNavigate } from '$app/navigation';
	import Button from '$lib/components/Button.svelte';

	const code = page.params.code ?? '';
	let players = $state<string[]>([]);
	let me = $state('');
	let isHost = $state(false);
	let copied = $state(false);
	let leaving = false;

	beforeNavigate((nav) => {
		if (leaving) return;
		if (nav.willUnload) return;
		if (confirm('Quitter le lobby ?')) {
			send({ type: 'leave' });
		} else {
			nav.cancel();
		}
	});

	function clearSessionData() {
		sessionStorage.removeItem('players');
	}

	onMount(() => {
		const savedPlayers = sessionStorage.getItem('players');
		if (savedPlayers) {
			try {
				players = JSON.parse(savedPlayers);
			} catch {
				players = [];
			}
		}

		const savedHost = sessionStorage.getItem('isHost');
		if (savedHost) isHost = savedHost === 'true';

		const unsubscribe = subscribe(handleMessage);

		send({ type: 'get_lobby', code });

		return () => {
			unsubscribe();
		};
	});

	function handleMessage(msg: any) {
		if (msg.type === 'lobby_info') {
			players = msg.players;
			me = msg.me;
			isHost = msg.host === msg.me;
			sessionStorage.setItem('isHost', isHost.toString());
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'player_joined') {
			if (!players.includes(msg.username)) players = [...players, msg.username];
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'player_left') {
			players = players.filter((player) => player !== msg.username);
			sessionStorage.setItem('players', JSON.stringify(players));
		}
		if (msg.type === 'lobby_closed') {
			clearSessionData();
			leaving = true;
			goto('/lobby');
		}
		if (msg.type === 'match_found') {
			game.id = msg.game_id;
			game.opponents = msg.opponent ?? [];
			game.players = msg.players ?? [];
			game.me = msg.me ?? '';
			game.word = msg.word;
			game.scores = {};
			game.is_ranked = msg.is_ranked ?? false;
			clearSessionData();
			sessionStorage.setItem('private_lobby_code', code);
			sessionStorage.removeItem('draw_in_progress');
			sessionStorage.setItem(
				'draw_ends_at',
				String(Date.now() + ((msg.duration ?? 60) + (msg.countdown ?? 0)) * 1000)
			);
			leaving = true;
			goto('/in-game');
		}
	}

	function shortName(name: string, max = 6) {
		return name.length > max ? name.slice(0, max) + '…' : name;
	}

	function startGame() {
		send({ type: 'start_game', code });
	}

	function copyCode() {
		if (!code) return;
		navigator.clipboard.writeText(code);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<svelte:head>
	<title>Lobby {code} — Draw Meter</title>
</svelte:head>

<div class="flex flex-1 items-center justify-center py-8">
	<div class="flex w-full max-w-[600px] flex-col gap-8 border-4 border-ink bg-bg p-6 shadow-nb-lg">
		<header class="text-center">
			<h1 class="mb-4 text-3xl uppercase">Private Game</h1>
			<div
				class="inline-flex flex-col items-center gap-1 border-4 border-ink bg-bg-alt px-6 py-3 shadow-nb-sm"
			>
				<span class="font-mono text-xs font-bold tracking-[0.2em] text-muted uppercase">
					Room Code
				</span>
				<button
					class="group flex cursor-pointer flex-col items-center gap-1 border-none bg-none p-0 font-mono"
					onclick={copyCode}
					title="Click to copy"
				>
					<span class="text-3xl font-bold tracking-[0.2em] text-ink uppercase">{code}</span>
					<span
						class="text-xs font-bold tracking-[0.1em] text-primary uppercase group-hover:underline"
					>
						{copied ? 'Copied ✓' : 'Copy'}
					</span>
				</button>
			</div>
		</header>

		<div
			class="flex flex-wrap items-center justify-center gap-4 border-4 border-ink bg-bg-alt px-6 py-8"
		>
			{#each players as player (player)}
				<div class="flex flex-[0_0_96px] flex-col items-center gap-3 text-center">
					<div
						class="flex h-20 w-20 items-center justify-center overflow-hidden border-4 border-ink bg-primary px-2 text-center font-display font-extrabold text-on-primary shadow-nb-sm"
						title={player}
					>
						{shortName(player)}
					</div>
				</div>
			{/each}
		</div>

		<div class="flex justify-center">
			{#if isHost}
				<Button
					variant="primary"
					onclick={startGame}
					disabled={players.length < 2}
					class="h-14 w-full text-xl"
				>
					{players.length < 2 ? 'Waiting for players…' : 'Start game'}
				</Button>
			{:else}
				<p class="text-sm text-muted italic">Waiting for the host to start…</p>
			{/if}
		</div>
	</div>
</div>
