	<script lang="ts">
		import { game } from '$lib/stores/game.svelte';
		import { send, subscribe, isOpen } from '$lib/stores/wsManager';
		import { onMount } from 'svelte';
		import Button from '$lib/components/Button.svelte';
		import { goto, beforeNavigate } from '$app/navigation';

	type Point = { x: number; y: number };
	type Trait = { color: string; width: number; points: Point[] };

	let canvas: HTMLCanvasElement = $state()!;
	let context: CanvasRenderingContext2D = $state()!;
	let last = $state<Point | null>(null);
	let stack = $state<Trait[]>([]);
	let redoStack = $state<Trait[]>([]);
	let result = $state<'winner' | 'looser' | 'draw' | null>(null);
	let elo_diff = $state(0);
	let timeLeft = $state(60);
	let showCountdown = $state(false);
	let countdownNum = $state(3);
	let myUsername = $state('');
	let myElo = $state<number | null>(null);
	let opponentElo = $state<number | null>(null);
	let endsAt = 0;
	let timerId: ReturnType<typeof setInterval> | null = null;
	let pointsSinceLastGuess = $state(0);
	let roundWins = $state<Record<string, number>>({});
	let disconnectedPlayers = $state<Record<string, boolean>>({});
	let back_lobby = $state(true);
	let exist = $state(true);
	let countdownTimers: ReturnType<typeof setTimeout>[] = [];
	let surrendered= $state(false);

	const GUESS_EVERY_POINTS = 10;
	const DRAW_COLOR = '#000000';
	const DRAW_WIDTH = 0.01;

	let currentRound = $derived(
		Object.values(roundWins).reduce((total, wins) => total + wins, 0) + 1
	);

	function readJson<T>(key: string, fallback: T) {
		const value = sessionStorage.getItem(key);
		if (!value) return fallback;
		try {
			return JSON.parse(value) as T;
		} catch {
			return fallback;
		}
	}

	function tick() {
		timeLeft = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
	}

	function startTimer() {
		if (timerId) clearInterval(timerId);
		tick();
		timerId = setInterval(tick, 250);
	}

	function stopTimer() {
		if (timerId) clearInterval(timerId);
		timerId = null;
	}

	function applyPlayers(players: string[]) {
		game.players = players;
		const scores = { ...game.scores };
		const wins = { ...roundWins };
		for (const player of players) {
			scores[player] = scores[player] ?? 0;
			wins[player] = wins[player] ?? 0;
		}
		game.scores = scores;
		roundWins = wins;
	}

	function scorePlayers() {
		if (game.players.length > 0) return game.players;
		const players: string[] = [];
		if (game.me || myUsername) players.push(game.me || myUsername);
		return players;
	}

	function isMe(player: string) {
		return player === game.me || player === myUsername;
	}

	function playerLabel(player: string) {
		return isMe(player) ? 'You' : player;
	}

	function scoreFor(player: string) {
		if (isMe(player)) return game.scores[player] ?? 0;
		return game.scores[player] ?? 0;
	}

	function setPlayerScore(username: string, score: number) {
		if (!username) return;
		const value = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
		game.scores = { ...game.scores, [username]: value };
		sessionStorage.setItem('draw_scores', JSON.stringify(game.scores));
	}

	function updateScores(scores: Record<string, number>) {
		game.scores = { ...scores };
		for (const player of scorePlayers()) {
			const score = scores[player] ?? 0;
		}
		sessionStorage.setItem('draw_scores', JSON.stringify(game.scores));
	}

	function resetScores() {
		const scores: Record<string, number> = {};
		for (const player of scorePlayers()) scores[player] = 0;
		updateScores(scores);
	}

	function opponentLabel() {
		const others = scorePlayers().filter((player) => !isMe(player));
		if (others.length === 1) return others[0];
		return `${scorePlayers().length} Players`;
	}

	function updateRoundWins(wins: Record<string, number>) {
		const nextWins = { ...wins };
		if (game.players.length === 0 && Object.keys(nextWins).length > 0) {
			applyPlayers(Object.keys(nextWins));
		}
		for (const player of scorePlayers()) nextWins[player] = nextWins[player] ?? 0;
		roundWins = nextWins;
		sessionStorage.setItem('draw_round_wins', JSON.stringify(roundWins));
	}

	function roundWinFor(player: string) {
		return roundWins[player] ?? 0;
	}

	function saveGameData() {
		sessionStorage.setItem('draw_word', game.word);
		sessionStorage.setItem('draw_opponents', JSON.stringify(game.opponents));
		sessionStorage.setItem('draw_players', JSON.stringify(game.players));
		sessionStorage.setItem('draw_me', game.me);
		sessionStorage.setItem('draw_scores', JSON.stringify(game.scores));
		sessionStorage.setItem('draw_round_wins', JSON.stringify(roundWins));
		sessionStorage.setItem('draw_is_ranked', game.is_ranked.toString());
	}

	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponents');
		sessionStorage.removeItem('draw_players');
		sessionStorage.removeItem('draw_me');
		sessionStorage.removeItem('draw_scores');
		sessionStorage.removeItem('draw_round_wins');
		sessionStorage.removeItem('draw_is_ranked');
		sessionStorage.removeItem('draw_ends_at');
		sessionStorage.removeItem('draw_in_progress');
		sessionStorage.removeItem('isHost');
	}

	function triggerCountdown() {
    	for (const t of countdownTimers) clearTimeout(t);
    	countdownTimers = [];
		showCountdown = true;
    	countdownNum = 3;
		countdownTimers.push(setTimeout(() => { countdownNum = 2; }, 1000));
    	countdownTimers.push(setTimeout(() => { countdownNum = 1; }, 2000));
    	countdownTimers.push(setTimeout(() => { countdownNum = 0; }, 3000));
    	countdownTimers.push(setTimeout(() => { showCountdown = false; }, 3600));
	}

	function loadSessionData() {
		stack = readJson<Trait[]>('draw_stack', []);
		game.scores = readJson<Record<string, number>>('draw_scores', {});
		roundWins = readJson<Record<string, number>>('draw_round_wins', {});

		const savedPlayers = readJson<string[]>('draw_players', []);
		if (savedPlayers.length > 0) applyPlayers(savedPlayers);

		const savedMe = sessionStorage.getItem('draw_me');
		if (savedMe) game.me = savedMe;

		const savedIsRanked = sessionStorage.getItem('draw_is_ranked');
		if (savedIsRanked) game.is_ranked = savedIsRanked === 'true';

		const savedWord = sessionStorage.getItem('draw_word');
		if (savedWord) game.word = savedWord;

		const savedOpponents = readJson<string[]>('draw_opponents', []);
		if (savedOpponents.length > 0) game.opponents = savedOpponents;

		const savedEndsAt = sessionStorage.getItem('draw_ends_at');
		endsAt = savedEndsAt ? parseInt(savedEndsAt) : Date.now() + 63000;
	}

	function loadUserData() {
		fetch('/api/session/', { credentials: 'same-origin' })
			.then((response) => response.json())
			.then((session) => {
				if (!session.authenticated || !session.user) return;
				const user = session.user;
				myUsername = user.username;
				myElo = user.elo;
				if (!game.me) game.me = user.username;
				if (!game.players.includes(user.username)) applyPlayers([user.username, ...game.players]);
			})
			.catch(() => {});
			if (!game.is_ranked || game.opponents.length === 0) return;
			fetch(`/api/users/${game.opponents[0]}/stats`, { credentials: 'same-origin' })
			.then((response) => (response.ok ? response.json() : null))
			.then((data) => {
				if (data) opponentElo = data.Elo;
			})
			.catch(() => {});
	}

	function fetchGameData() {
		send({ type: 'get_info' });
		console.log("called get info");
	}

		beforeNavigate((nav) => {
			if (result) return;
			if (nav.willUnload) return;
			if (!exist) return;
			if (surrendered) return;
			if (confirm('Quitter la partie ? Tu déclares forfait.')) {
				send({ type: 'surrender' , leave_lobby: true});
			} else {
				nav.cancel();
			}
		});

		onMount(() => {
			const isReconnect = sessionStorage.getItem('draw_in_progress') === '1';
			console.log("isReconnect: ", isReconnect)
			sessionStorage.setItem('draw_in_progress', '1');
			loadSessionData();
			startTimer();
			loadUserData();
			fetchGameData();
			

			if (!isReconnect) {
				triggerCountdown();
			}
			send({ type: 'get_info' });
			const code = sessionStorage.getItem('private_lobby_code');
			if (code)
				send({ type: 'get_lobby', code });
			const unsubscribe = subscribe((msg: any) => {
				console.log(msg)
				switch (msg.type) {
					case 'ai_guess':
						setPlayerScore(
							msg.username,
							msg.scores ?? msg.guess?.[game.word] ?? 0
						);
						break;
					case 'player_guess':
						setPlayerScore(msg.username, msg.score ?? msg.guess?.[game.word] ?? 0);
						break;
					case 'opponent_disconnected':
						disconnectedPlayers[msg.username] = true;
						break;
					case 'opponent_reconnected':
						delete disconnectedPlayers[msg.username];
						break;
					case 'reconnect_game':
						game.id = msg.game_id;
						game.opponents = Array.isArray(msg.opponent) ? msg.opponent : (msg.opponent ? [msg.opponent] : []);
						game.me = msg.me ?? game.me;
						game.word = msg.word;
						game.is_ranked = msg.is_ranked ?? game.is_ranked;
						delete disconnectedPlayers[msg.me];
						applyPlayers(msg.players ?? []);
						updateScores(msg.scores ?? {});
						updateRoundWins(msg.round_wins ?? {});
						saveGameData();
						if (msg.time_left != null) {
							endsAt = Date.now() + msg.time_left * 1000;
							sessionStorage.setItem('draw_ends_at', String(endsAt));
							startTimer();
						}
						break;
					case 'next_round':
						game.word = msg.word;
						if (msg.scores) updateScores(msg.scores);
						else resetScores();
						updateRoundWins(msg.round_wins ?? roundWins);
						sessionStorage.setItem('draw_word', game.word);
						stack = [];
						redoStack = [];
						last = null;
						pointsSinceLastGuess = 0;
						if (context) redraw();
						if (msg.duration != null) {
							endsAt = Date.now() + (msg.duration + (msg.countdown ?? 0)) * 1000;
							sessionStorage.setItem('draw_ends_at', String(endsAt));
							startTimer();
						}
						triggerCountdown();
						break;
					case 'end_game':
						stopTimer();
						elo_diff = msg.elo_diff;
						result = msg.status;
						setTimeout(() => {
							backAfterGame();
						}, 3000);
						clearSessionData();
						break;
					case 'lobby_closed':
						back_lobby = false;
						break;
					case 'game_info':
						console.log("received game_info");
						if (!msg.exist) {
							exist = false;
							const code = sessionStorage.getItem('private_lobby_code');
							console.log(code);
							if (code != '' && back_lobby == true)
								goto(code ? `/lobby/${code}` : '/lobby');
							else
								goto("/");
							break;
						}
						console.log("game exists, loading data: \n" + msg);
						game.id = msg.game_id;
						game.opponents = msg.opponent ?? [];
						game.me = msg.me;
						game.word = msg.word;
						game.is_ranked = msg.is_ranked
						applyPlayers(msg.players);
						updateScores(msg.scores);
						updateRoundWins(msg.round_wins);
						if (msg.time_left != null) {
							endsAt = Date.now() + msg.time_left * 1000;
							sessionStorage.setItem('draw_ends_at', String(endsAt));
							startTimer();
						}
						saveGameData();
						startTimer();
						loadUserData();
						break;
				default : 
					console.log("unexpected WS msg: ", msg);
				}				
			});

			return () => {
				unsubscribe();
				stopTimer();
				for (const t of countdownTimers) clearTimeout(t);
			};
		});

	$effect(() => {
		sessionStorage.setItem('draw_stack', JSON.stringify(stack));
	});

	$effect(() => {
		if (canvas) {
			context = canvas.getContext('2d')!;
			resize();
		}
	});

	function surrender() {
		if (confirm('Are you sure you want to forfeit the match?')) {
			const isHost = sessionStorage.getItem('isHost') === 'true';
			send({ type: 'surrender' , leave_lobby: isHost});
			surrendered = true;
			const code = sessionStorage.getItem('private_lobby_code');
			console.log(code);
			clearSessionData();
			if (!game.is_ranked && code != '' && back_lobby == true && !isHost)
				goto(code ? `/lobby/${code}` : '/lobby');
			else
				goto("/");
				
		}
	}

	function resize() {
		if (!canvas || !context) return;
		const dpr = window.devicePixelRatio || 1;
		canvas.width = Math.floor(canvas.clientWidth * dpr);
		canvas.height = Math.floor(canvas.clientHeight * dpr);
		context.setTransform(dpr, 0, 0, dpr, 0, 0);
		redraw();
	}

	function canvasPoint(event: PointerEvent) {
		return {
			x: event.offsetX / canvas.clientWidth,
			y: event.offsetY / canvas.clientHeight
		};
	}

	function drawLine(from: Point, to: Point, trait: Trait) {
		context.strokeStyle = trait.color;
		context.lineWidth = trait.width * canvas.clientWidth;
		context.lineCap = 'round';
		context.lineJoin = 'round';
		context.beginPath();
		context.moveTo(from.x * canvas.clientWidth, from.y * canvas.clientHeight);
		context.lineTo(to.x * canvas.clientWidth, to.y * canvas.clientHeight);
		context.stroke();
	}

	function redraw() {
		context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);

		for (const trait of stack) {
			if (trait.points.length === 0) continue;

			context.strokeStyle = trait.color;
			context.lineWidth = trait.width * canvas.clientWidth;
			context.lineCap = 'round';
			context.lineJoin = 'round';
			context.beginPath();
			context.moveTo(
				trait.points[0].x * canvas.clientWidth,
				trait.points[0].y * canvas.clientHeight
			);
			for (let index = 1; index < trait.points.length; index += 1) {
				context.lineTo(
					trait.points[index].x * canvas.clientWidth,
					trait.points[index].y * canvas.clientHeight
				);
			}
			context.stroke();
		}
	}

	function undo() {
		const trait = stack.pop();
		if (!trait) return;
		redoStack.push(trait);
		redraw();
		makeAiGuess();
	}

	function redo() {
		const trait = redoStack.pop();
		if (!trait) return;
		stack.push(trait);
		redraw();
		makeAiGuess();
	}

	function clearDrawing() {
		stack = [];
		redoStack = [];
		last = null;
		pointsSinceLastGuess = 0;
		redraw();
		makeAiGuess();
	}

		function makeAiGuess() {
			send({ type: 'guess', strokes: stack });
		}

	function finishStroke() {
		if (!last) return;

		last = null;
		pointsSinceLastGuess = 0;
		makeAiGuess();
	}

	function backAfterGame() {
		if (game.is_ranked || !back_lobby) {
			goto('/');
			return;
		}
		const code = sessionStorage.getItem('private_lobby_code');
		goto(code ? `/lobby/${code}` : '/lobby');
	}

	const toolBase =
		'flex cursor-pointer items-center justify-center border-4 border-ink bg-bg leading-none shadow-nb-sm transition-[translate,box-shadow] duration-[120ms] ease-out h-[var(--tool-size)] w-[var(--tool-size)] p-0 hover:not-disabled:-translate-x-0.5 hover:not-disabled:-translate-y-0.5 hover:not-disabled:shadow-nb active:not-disabled:translate-x-[3px] active:not-disabled:translate-y-[3px] active:not-disabled:shadow-none disabled:cursor-not-allowed disabled:opacity-35 disabled:shadow-none';
	const toolIconClasses = `${toolBase} text-[calc(var(--tool-size)*0.25)]`;
	const toolTextClasses = `${toolBase} font-mono text-[10px] font-bold uppercase`;
</script>

<svelte:window onresize={resize} />

{#if showCountdown}
	<div
		class="group fixed inset-0 z-[900] grid grid-rows-[32vh_1fr_16vh] overflow-hidden bg-bg sm:grid-rows-[28vh_1fr_18vh]"
		data-count={countdownNum}
		aria-live="assertive"
		aria-atomic="true"
	>
		<div class="flex flex-wrap border-b-4 border-ink">
			{#each scorePlayers() as player, index (player)}
				<div
					class="flex min-w-[20%] flex-1 animate-cd-half-in flex-col justify-center gap-2 p-4 sm:px-12 sm:py-6 {isMe(
						player
					)
						? ''
						: 'items-end text-right [animation-delay:0.06s]'}"
				>
					<span class="font-mono text-xs font-bold tracking-[0.22em] text-muted uppercase">
						Player {String(index + 1).padStart(2, '0')}
					</span>
					<span
						class="max-w-[42vw] overflow-hidden font-display text-[clamp(1.1rem,5.5vw,2rem)] leading-none font-extrabold text-ellipsis whitespace-nowrap uppercase sm:text-[clamp(1.6rem,4.5vw,3.5rem)] {isMe(
							player
						)
							? 'text-primary'
							: 'text-danger'}"
					>
						{playerLabel(player)}
					</span>
					{#if game.is_ranked}
						<span class="font-mono text-2xl font-bold text-ink">
							{isMe(player) ? (myElo ?? '-') : (opponentElo ?? '-')}<em
								class="ml-1 text-xs font-normal tracking-[0.12em] text-muted not-italic">ELO</em
							>
						</span>
					{/if}
				</div>
			{/each}
		</div>

		<div
			class="flex items-center justify-center border-b-4 border-ink group-data-[count=0]:bg-success group-data-[count=1]:bg-danger group-data-[count=2]:bg-bg-alt group-data-[count=3]:bg-accent"
		>
			{#key countdownNum}
				<div
					class="pointer-events-none font-display leading-none font-extrabold text-ink select-none group-data-[count=1]:text-white {countdownNum ===
					0
						? 'animate-cd-go-blast text-[min(20vh,30vw)] sm:text-[min(22vh,18vw)]'
						: 'animate-cd-num-stamp text-[min(42vh,54vw)] sm:text-[min(48vh,40vw)]'}"
				>
					{countdownNum === 0 ? 'GO!' : countdownNum}
				</div>
			{/key}
		</div>

		<div class="flex animate-cd-bot-in items-center justify-center gap-6 bg-ink px-8">
			<span class="font-mono text-sm font-bold tracking-[0.28em] text-white/40 uppercase">Draw</span
			>
			<span
				class="font-display text-[clamp(1.4rem,7vw,2.2rem)] font-extrabold tracking-[0.03em] text-accent uppercase sm:text-[clamp(2rem,5vw,4rem)]"
			>
				{game.word}
			</span>
		</div>
	</div>
{/if}

<header
	class="mb-6 flex flex-col items-center gap-3 border-b-4 border-ink bg-bg p-4 md:flex-row md:justify-between md:gap-0 md:px-8"
>
	<div class="flex flex-none flex-wrap items-center justify-center gap-4 md:flex-1">
		<h1 class="text-3xl uppercase">Draw!</h1>
		<div class="flex flex-col gap-2">
			<div
				class="border-4 border-ink bg-bg-alt px-3 py-2 font-mono text-sm font-bold text-muted uppercase shadow-nb-sm"
			>
				VS <strong class="text-ink">{opponentLabel()}</strong>
			</div>
			{#if scorePlayers().length > 1}
				<div class="flex items-start gap-3 font-mono text-xs font-bold text-muted uppercase">
					<span class="whitespace-nowrap">Round {currentRound}</span>
					<div class="flex flex-col gap-1">
						{#each scorePlayers() as player (player)}
							<div class="flex min-w-[130px] items-center justify-between gap-2">
								<span class="max-w-[90px] overflow-hidden text-ellipsis whitespace-nowrap">
									{playerLabel(player)}
								</span>
								<div class="flex items-center gap-[5px]">
									{#each [1, 2] as win (win)}
										<div
											class="h-3 w-3 rounded-full border-2 transition-colors duration-300 {isMe(
												player
											)
												? 'border-primary'
												: 'border-danger'} {roundWinFor(player) >= win
												? isMe(player)
													? 'bg-primary'
													: 'bg-danger'
												: 'bg-transparent'}"
										></div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class="flex flex-none flex-col items-center justify-center gap-1 text-center md:flex-[2]">
		<div
			class="font-mono text-3xl font-bold tabular-nums transition-colors duration-[120ms] {timeLeft <=
			10
				? 'animate-timer-pulse text-danger'
				: 'text-ink'}"
		>
			{Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
		</div>
		<span class="text-xs font-bold tracking-[0.2em] text-muted uppercase">You are drawing</span>
		<div
			class="border-4 border-ink bg-accent px-4 py-1 font-display text-3xl leading-tight font-extrabold tracking-[0.04em] text-ink uppercase shadow-nb-sm"
		>
			{game.word}
		</div>
	</div>

	<div class="flex flex-none justify-center md:flex-1 md:justify-end">
		<Button variant="danger" onclick={surrender}>Surrender</Button>
	</div>
</header>

{#if result}
	<div class="fixed inset-0 z-[1000] flex items-center justify-center bg-scrim">
		<div
			class="m-4 animate-pop-in border-4 border-ink px-6 py-8 text-center shadow-nb-lg md:px-16 md:py-12 {result ===
			'winner'
				? 'bg-success'
				: result === 'looser'
					? 'bg-danger text-on-danger'
					: 'bg-accent'}"
		>
			{#if result === 'winner'}
				<h2 class="text-5xl uppercase">You Won!</h2>
				<p class="mt-3 mb-8 font-mono text-xl font-bold">
					{game.is_ranked ? `+${elo_diff} Elo` : 'No Elo change'}
				</p>
			{:else if result === 'draw'}
				<h2 class="text-5xl uppercase">Draw</h2>
				<p class="mt-3 mb-8 font-mono text-xl font-bold">No Elo change</p>
			{:else}
				<h2 class="text-5xl uppercase">You Lost</h2>
				<p class="mt-3 mb-8 font-mono text-xl font-bold">
					{game.is_ranked ? `${elo_diff} Elo` : 'No Elo change'}
				</p>
			{/if}
			<Button variant="primary" onclick={backAfterGame}>
				{game.is_ranked ? 'Back to Home' : 'Back to Lobby'}
			</Button>
		</div>
	</div>
{/if}

<div
	class="grid grid-cols-[auto_auto] items-center justify-center justify-items-center gap-3 gap-x-4 p-3 [--canvas-side:78vmin] [--tool-size:calc(var(--canvas-side)*0.1)] md:flex md:gap-8 md:p-4 md:[--canvas-side:50vmin]"
>
	<div
		class="col-start-1 row-start-2 grid grid-cols-[repeat(3,var(--tool-size))] gap-2 md:col-auto md:row-auto"
	>
		<button
			class={toolIconClasses}
			onclick={undo}
			disabled={stack.length === 0}
			aria-label="Undo"
			title="Undo"
		>
			↶
		</button>
		<button
			class={toolIconClasses}
			onclick={redo}
			disabled={redoStack.length === 0}
			aria-label="Redo"
			title="Redo"
		>
			↷
		</button>
		<button
			class={toolTextClasses}
			onclick={clearDrawing}
			disabled={stack.length === 0 && redoStack.length === 0}
			aria-label="Clear"
			title="Clear"
		>
			Clear
		</button>
	</div>

	<canvas
		class="col-span-full row-start-1 h-[var(--canvas-side)] w-[var(--canvas-side)] cursor-crosshair touch-none border-4 border-ink bg-bg shadow-nb md:col-auto md:row-auto"
		bind:this={canvas}
		onpointerdown={(event) => {
			const point = canvasPoint(event);
			stack.push({
				color: DRAW_COLOR,
				width: DRAW_WIDTH,
				points: [point]
			});
			redoStack = [];
			last = point;
		}}
		onpointerup={finishStroke}
		onpointerleave={finishStroke}
		onpointermove={(event) => {
			if (event.buttons !== 1 || !last) return;

			const point = canvasPoint(event);
			const trait = stack[stack.length - 1];
			drawLine(last, point, trait);
			trait.points.push(point);
			last = point;
			pointsSinceLastGuess += 1;

			if (pointsSinceLastGuess >= GUESS_EVERY_POINTS) {
				pointsSinceLastGuess = 0;
				makeAiGuess();
			}
		}}
	></canvas>

	<div
		class="col-start-2 row-start-2 flex max-h-[var(--canvas-side)] max-w-[calc(var(--tool-size)*6)] flex-wrap justify-center gap-4 overflow-y-auto md:col-auto md:row-auto"
	>
		{#each scorePlayers() as player (player)}
			<div
				class="flex flex-col items-center gap-2 {disconnectedPlayers[player]
					? 'opacity-40 grayscale transition-all duration-300'
					: ''}"
			>
				<span class="font-mono text-xl font-bold tabular-nums">
					{Math.round(scoreFor(player) ?? 0)}%
				</span>
				<div
					class="relative h-[calc(var(--canvas-side)-4rem)] w-[var(--tool-size)] overflow-hidden border-4 border-ink bg-bg-alt shadow-nb-sm"
				>
					<div
						class="absolute bottom-0 left-0 w-full transition-[height] duration-300 {isMe(player)
							? 'bg-[repeating-linear-gradient(45deg,var(--color-primary)_0_14px,var(--color-primary-dark)_14px_28px)]'
							: 'bg-[repeating-linear-gradient(45deg,var(--color-danger)_0_14px,var(--color-danger-dark)_14px_28px)]'}"
						style="height: {scoreFor(player) ?? 0}%"
					></div>
				</div>
				<span
					class="max-w-[calc(var(--tool-size)*1.6)] overflow-hidden font-display text-xs font-bold tracking-[0.05em] text-ellipsis whitespace-nowrap uppercase {isMe(
						player
					)
						? 'text-primary'
						: 'text-danger'}"
				>
					{#if disconnectedPlayers[player]}
						<span class="text-[0.7em] opacity-80">(Offline)</span>
					{/if}
					{playerLabel(player)}
				</span>
			</div>
		{/each}
	</div>
</div>
