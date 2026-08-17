<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { connect, send, subscribe } from '$lib/stores/wsManager';

	let username = $state('');
	let showRejoin = $state(false);
	let rejoinGame = $state({
	opponents: [],
	players: [] as string[],
	time_left: 0,
	is_ranked: false,
	word: '',
	scores: {},
	round_wins: {}
	});


	const tileBase =
		'group flex items-center justify-between gap-4 border-4 border-ink p-6 font-display text-2xl font-extrabold uppercase no-underline shadow-nb transition-[translate,box-shadow] duration-[120ms] ease-out hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-nb-lg active:translate-x-[3px] active:translate-y-[3px] active:shadow-none';

	const popupBtnBase =
		'flex-1 cursor-pointer border-4 border-ink p-4 font-display text-sm font-bold text-on-primary uppercase transition-[translate,box-shadow] duration-[120ms] ease-out hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-nb active:translate-x-[3px] active:translate-y-[3px] active:shadow-none';

	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponents');
		sessionStorage.removeItem('draw_players');
		sessionStorage.removeItem('draw_me');
		sessionStorage.removeItem('draw_scores');
		sessionStorage.removeItem('draw_is_ranked');
		sessionStorage.removeItem('draw_ends_at');
		sessionStorage.removeItem('draw_in_progress');
		sessionStorage.removeItem('isHost');
		sessionStorage.removeItem('players');
		sessionStorage.removeItem('draw_round_wins')
	}

	function rejoin() {
		sessionStorage.setItem('draw_word', rejoinGame.word);
		sessionStorage.setItem('draw_opponents', JSON.stringify(rejoinGame.opponents));
		sessionStorage.setItem('draw_players', JSON.stringify(rejoinGame.players));
		sessionStorage.setItem('draw_me', username);
		sessionStorage.setItem('draw_is_ranked', rejoinGame.is_ranked.toString());
		sessionStorage.setItem('draw_scores', JSON.stringify(rejoinGame.scores));
		sessionStorage.setItem('draw_round_wins', JSON.stringify(rejoinGame.round_wins));
		sessionStorage.setItem('draw_in_progress', '1');
		if (rejoinGame.time_left > 0)
			sessionStorage.setItem('draw_ends_at', String(Date.now() + rejoinGame.time_left * 1000));
		goto('/in-game');
	}

	function forfeit() {
		send({ type: 'surrender', leave_lobby: true});
		showRejoin = false;
	}

		onMount(async () => {
			let authenticated = false;
		try {
			const response = await fetch('/api/session/', {
				method: 'GET',
				credentials: 'same-origin'
			});
				const session = await response.json();
				if (session.authenticated && session.user) {
					username = session.user.username;
					authenticated = true;
				}
				} catch {
				return;
				}

				if (!authenticated) return;

				connect();

				let unsub = () => {};
				const timeout = setTimeout(() => unsub(), 3000);

				unsub = subscribe((msg: any) => {
				if (msg.type !== 'reconnect_game') return;
					clearTimeout(timeout);
					unsub();
					rejoinGame = {
						opponents: msg.opponent || [],
						players: msg.players || [],
						time_left: msg.time_left ?? 0,
						is_ranked: msg.is_ranked ?? false,
						word: msg.word || '',
						scores: msg.scores || {},
						round_wins: msg.round_wins || {}
					};
				showRejoin = true;
				});

				return () => {
					clearTimeout(timeout);
					unsub();
				};
				});
		</script>

{#if showRejoin}
	<div
		class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
		role="dialog"
		aria-label="Game reconnection"
	>
		<div class="w-[90%] max-w-[400px] border-4 border-ink bg-bg p-12 text-center shadow-nb-lg">
			<h2 class="mb-4 font-display text-2xl uppercase">You have an active game</h2>
			<p class="mb-2 text-muted">
				vs {rejoinGame.opponents ||
					rejoinGame.players.filter((p: string) => p !== username).join(', ') ||
					'opponents'}
			</p>
			{#if rejoinGame.time_left > 0}
				<p class="mb-2 text-muted">{Math.ceil(rejoinGame.time_left)}s remaining</p>
			{/if}
			<div class="mt-8 flex gap-4">
				<button class="{popupBtnBase} bg-primary" onclick={rejoin}>Rejoin</button>
				<button class="{popupBtnBase} bg-danger" onclick={forfeit}>Surrender</button>
			</div>
		</div>
	</div>
{/if}

<div class="flex flex-1 flex-col items-center justify-center gap-12 py-8">
	<header class="max-w-[520px] text-center">
		<p class="mb-3 font-mono text-xs font-bold tracking-[0.25em] text-muted uppercase">
			Draw Meter
		</p>
		<h1 class="text-3xl uppercase md:text-5xl">
			Welcome
			<span class="inline-block -rotate-[1.5deg] border-4 border-ink bg-accent px-2 shadow-nb-sm"
				>{username || 'Guest'}</span
			>
		</h1>
		<p class="mt-4 text-xl text-muted">Draw fast. Win first. Outsmart the AI.</p>
	</header>

	<main class="flex w-full max-w-[440px] flex-col gap-4">
		<a href="/start_game" class="{tileBase} bg-primary text-on-primary">
			<span>Play Now!</span>
			<span
				class="text-3xl leading-none transition-[translate] duration-[120ms] group-hover:translate-x-2"
				aria-hidden="true">→</span
			>
		</a>

		<a href="/lobby" class="{tileBase} bg-accent text-ink">
			<span>Private Game</span>
			<span
				class="text-3xl leading-none transition-[translate] duration-[120ms] group-hover:translate-x-2"
				aria-hidden="true">→</span
			>
		</a>

		<a href="/ranking" class="{tileBase} bg-highlight text-on-primary">
			<span>Leaderboard</span>
			<span
				class="text-3xl leading-none transition-[translate] duration-[120ms] group-hover:translate-x-2"
				aria-hidden="true">→</span
			>
		</a>
	</main>
</div>
