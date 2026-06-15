<script lang="ts">
	import { game } from '$lib/stores/game.svelte';
	import { getWs, setWs } from '$lib/stores/ws';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

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

	const GUESS_EVERY_POINTS = 10;
	const DRAW_COLOR = '#000000';
	const DRAW_WIDTH = 0.01;

	let currentRound = $derived(
		Object.values(roundWins).reduce((total, wins) => total + wins, 0) + 1
	);

	function handleHardExit() {
		if (!result) {
			const ws = getWs();
			if (ws && ws.readyState === WebSocket.OPEN) {
				ws.send(JSON.stringify({ type: 'surrender' }));
			}
		}
	}

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
		if (game.opponent) players.push(game.opponent);
		return players;
	}

	function isMe(player: string) {
		return player === game.me || player === myUsername;
	}

	function playerLabel(player: string) {
		return isMe(player) ? 'You' : player;
	}

	function scoreFor(player: string) {
		if (isMe(player)) return game.scores[player] ?? game.my_score ?? 0;
		return game.scores[player] ?? (player === game.opponent ? game.opponent_score : 0);
	}

	function setPlayerScore(username: string, score: number) {
		if (!username) return;
		const value = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
		game.scores = { ...game.scores, [username]: value };
		if (isMe(username)) game.my_score = value;
		if (username === game.opponent) game.opponent_score = value;
		sessionStorage.setItem('draw_scores', JSON.stringify(game.scores));
	}

	function updateScores(scores: Record<string, number>) {
		game.scores = { ...scores };
		for (const player of scorePlayers()) {
			const score = scores[player] ?? 0;
			if (isMe(player)) game.my_score = score;
			if (player === game.opponent) game.opponent_score = score;
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
		if (others.length === 0) return 'Solo';
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
		sessionStorage.setItem('draw_opponent', game.opponent);
		sessionStorage.setItem('draw_players', JSON.stringify(game.players));
		sessionStorage.setItem('draw_me', game.me);
		sessionStorage.setItem('draw_scores', JSON.stringify(game.scores));
		sessionStorage.setItem('draw_round_wins', JSON.stringify(roundWins));
		sessionStorage.setItem('draw_is_ranked', game.is_ranked.toString());
	}

	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_my_score');
		sessionStorage.removeItem('draw_opp_score');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponent');
		sessionStorage.removeItem('draw_players');
		sessionStorage.removeItem('draw_me');
		sessionStorage.removeItem('draw_scores');
		sessionStorage.removeItem('draw_round_wins');
		sessionStorage.removeItem('draw_is_ranked');
		sessionStorage.removeItem('draw_ends_at');
	}

	function triggerCountdown() {
		showCountdown = true;
		countdownNum = 3;
		setTimeout(() => {
			countdownNum = 2;
		}, 1000);
		setTimeout(() => {
			countdownNum = 1;
		}, 2000);
		setTimeout(() => {
			countdownNum = 0;
		}, 3000);
		setTimeout(() => {
			showCountdown = false;
		}, 3600);
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

		const savedOpponent = sessionStorage.getItem('draw_opponent');
		if (savedOpponent) game.opponent = savedOpponent;

		const savedEndsAt = sessionStorage.getItem('draw_ends_at');
		endsAt = savedEndsAt ? parseInt(savedEndsAt) : Date.now() + 63000;
	}

	function loadUserData() {
		fetch('/api/users/me/', { credentials: 'same-origin' })
			.then((response) => (response.ok ? response.json() : null))
			.then((data) => {
				if (!data) return;
				myUsername = data.username;
				myElo = data.elo;
				if (!game.me) game.me = data.username;
				if (!game.players.includes(data.username)) applyPlayers([data.username, ...game.players]);
			})
			.catch(() => {});

		if (!game.is_ranked || !game.opponent) return;

		fetch(`/api/users/${game.opponent}/stats`, { credentials: 'same-origin' })
			.then((response) => (response.ok ? response.json() : null))
			.then((data) => {
				if (data) opponentElo = data.Elo;
			})
			.catch(() => {});
	}

	onMount(() => {
		const isReconnect = !!sessionStorage.getItem('draw_word');
		loadSessionData();
		startTimer();

		if (!isReconnect) {
			triggerCountdown();
			loadUserData();
		}

		let ws = getWs();
		if (!ws || ws.readyState !== WebSocket.OPEN) {
			ws = new WebSocket('/ws/');
			setWs(ws);
		}

		ws.onmessage = (event) => {
			const msg = JSON.parse(event.data);
			switch (msg.type) {
				case 'ai_guess':
					setPlayerScore(
						game.me || myUsername || msg.username,
						msg.score ?? msg.guess?.[game.word] ?? 0
					);
					break;
				case 'player_guess':
					setPlayerScore(msg.username, msg.score ?? msg.guess?.[game.word] ?? 0);
					break;
				case 'opponent_guess':
					setPlayerScore(game.opponent, msg.score ?? msg.guess?.[game.word] ?? 0);
					break;
				case 'opponent_disconnected':
					disconnectedPlayers[msg.username] = true;
					break;
				case 'reconnect_game':
					game.id = msg.game_id;
					game.opponent = msg.opponent;
					game.me = msg.me ?? game.me;
					game.word = msg.word;
					game.is_ranked = msg.is_ranked ?? game.is_ranked;
					disconnectedPlayers = {};
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
						endsAt = Date.now() + msg.duration * 1000;
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
				default:
					console.log(msg);
			}
		};

		return () => stopTimer();
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
			const ws = getWs();
			ws?.send(JSON.stringify({ type: 'surrender' }));
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
		const ws = getWs();
		ws?.send(JSON.stringify({ type: 'guess', strokes: stack }));
	}

	function finishStroke() {
		if (!last) return;

		last = null;
		pointsSinceLastGuess = 0;
		makeAiGuess();
	}

	function backAfterGame() {
		if (game.is_ranked) {
			goto('/');
			return;
		}
		const code = sessionStorage.getItem('private_lobby_code');
		goto(code ? `/lobby/${code}` : '/lobby');
	}
</script>

<svelte:window onresize={resize} onbeforeunload={handleHardExit} />

{#if showCountdown}
	<div class="cd-page" data-count={countdownNum} aria-live="assertive" aria-atomic="true">
		<div class="cd-top">
			{#each scorePlayers() as player, index (player)}
				<div class="cd-half" class:cd-you={isMe(player)} class:cd-opp={!isMe(player)}>
					<span class="cd-tag">Player {String(index + 1).padStart(2, '0')}</span>
					<span class="cd-pname">{playerLabel(player)}</span>
					{#if game.is_ranked && isMe(player)}
						<span class="cd-pelo">{myElo !== null ? myElo : '-'}<em>ELO</em></span>
					{:else if game.is_ranked && player === game.opponent}
						<span class="cd-pelo">{opponentElo !== null ? opponentElo : '-'}<em>ELO</em></span>
					{/if}
				</div>
			{/each}
		</div>

		<div class="cd-mid">
			{#key countdownNum}
				<div class="cd-num" class:cd-go={countdownNum === 0}>
					{countdownNum === 0 ? 'GO!' : countdownNum}
				</div>
			{/key}
		</div>

		<div class="cd-bot">
			<span class="cd-draw-tag">Draw</span>
			<span class="cd-draw-word">{game.word}</span>
		</div>
	</div>
{/if}

<header class="game-header">
	<div class="header-left">
		<h1>Draw!</h1>
		<div class="match-info">
			<div class="vs-badge">
				VS <strong>{opponentLabel()}</strong>
			</div>
			{#if scorePlayers().length > 1}
				<div class="bo3-tracker">
					<span class="round-text">Round {currentRound}</span>
					<div class="multiplayer-circles">
						{#each scorePlayers() as player (player)}
							<div class="player-bo3-row">
								<span class="bo3-name">{playerLabel(player)}</span>
								<div class="circles">
									<div
										class="circle"
										class:filled={roundWinFor(player) >= 1}
										class:opp={!isMe(player)}
									></div>
									<div
										class="circle"
										class:filled={roundWinFor(player) >= 2}
										class:opp={!isMe(player)}
									></div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class="header-center">
		<div class="timer" class:low={timeLeft <= 10}>
			{Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
		</div>
		<span class="word-label">You are drawing</span>
		<div class="target-word">{game.word}</div>
	</div>

	<div class="header-right">
		<button class="nb-btn nb-btn--danger" onclick={surrender}>Surrender</button>
	</div>
</header>

{#if result}
	<div class="overlay">
		<div
			class="modal"
			class:modal--win={result === 'winner'}
			class:modal--lose={result === 'looser'}
			class:modal--draw={result === 'draw'}
		>
			{#if result === 'winner'}
				<h2 class="result-text">You Won!</h2>
				{#if game.is_ranked}
					<p class="elo-text positive">+{elo_diff} Elo</p>
				{:else}
					<p class="elo-text">No Elo change</p>
				{/if}
			{:else if result === 'draw'}
				<h2 class="result-text">Draw</h2>
				<p class="elo-text">No Elo change</p>
			{:else}
				<h2 class="result-text">You Lost</h2>
				{#if game.is_ranked}
					<p class="elo-text negative">{elo_diff} Elo</p>
				{:else}
					<p class="elo-text">No Elo change</p>
				{/if}
			{/if}
			<button class="nb-btn nb-btn--primary" onclick={backAfterGame}>
				{game.is_ranked ? 'Back to Home' : 'Back to Lobby'}
			</button>
		</div>
	</div>
{/if}

<div class="game">
	<div class="tools">
		<button onclick={undo} disabled={stack.length === 0} aria-label="Undo" title="Undo">↶</button>
		<button onclick={redo} disabled={redoStack.length === 0} aria-label="Redo" title="Redo"
			>↷</button
		>
		<button
			class="clear-btn"
			onclick={clearDrawing}
			disabled={stack.length === 0 && redoStack.length === 0}
			aria-label="Clear"
			title="Clear"
		>
			Clear
		</button>
	</div>

	<canvas
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

	<div class="bars">
		{#each scorePlayers() as player (player)}
			<div class="meter" class:offline={disconnectedPlayers[player]}>
				<span class="meter-value">{Math.round(scoreFor(player) ?? 0)}%</span>
				<div class="loaderBar" class:loaderBar--opponent={!isMe(player)}>
					<div class="loaderBar-fill" style="height: {scoreFor(player) ?? 0}%"></div>
				</div>
				<span
					class="meter-label"
					class:meter-label--you={isMe(player)}
					class:meter-label--opponent={!isMe(player)}
				>
					{#if disconnectedPlayers[player]}
						<span style="font-size: 0.7em; opacity: 0.8;">(Offline)</span>
					{/if}
					{playerLabel(player)}
				</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.match-info {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.bo3-tracker {
		display: flex;
		align-items: flex-start;
		gap: var(--space-3);
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		color: var(--c-muted);
		text-transform: uppercase;
		font-weight: var(--fw-bold);
	}

	.round-text {
		white-space: nowrap;
	}

	.multiplayer-circles {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.player-bo3-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-2);
		min-width: 130px;
	}

	.bo3-name {
		max-width: 90px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.circles {
		display: flex;
		align-items: center;
		gap: 5px;
	}

	.circle {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: 2px solid var(--c-primary);
		background: transparent;
		transition: background 0.3s ease;
	}

	.circle.filled {
		background: var(--c-primary);
	}

	.circle.opp {
		border-color: var(--c-danger);
	}

	.circle.opp.filled {
		background: var(--c-danger);
	}

	.game-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-4) var(--space-6);
		background: var(--c-bg);
		border-bottom: var(--border-lg);
		margin-bottom: var(--space-5);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		flex: 1;
	}

	.game-header h1 {
		margin: 0;
		font-size: var(--fs-2xl);
		text-transform: uppercase;
	}

	.vs-badge {
		background: var(--c-bg-alt);
		color: var(--c-muted);
		padding: var(--space-2) var(--space-3);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		font-family: var(--font-mono);
		font-size: var(--fs-sm);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
	}

	.vs-badge strong {
		color: var(--c-ink);
	}

	.header-center {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 2;
		text-align: center;
		gap: var(--space-1);
	}

	.timer {
		font-family: var(--font-mono);
		font-size: var(--fs-2xl);
		font-weight: var(--fw-bold);
		font-variant-numeric: tabular-nums;
		color: var(--c-ink);
		transition: color var(--transition);
	}

	.timer.low {
		color: var(--c-danger);
		animation: timer-pulse 1s ease-in-out infinite;
	}

	@keyframes timer-pulse {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.12);
		}
	}

	.word-label {
		font-size: var(--fs-xs);
		text-transform: uppercase;
		font-weight: var(--fw-bold);
		color: var(--c-muted);
		letter-spacing: 0.2em;
	}

	.target-word {
		font-family: var(--font-display);
		font-size: var(--fs-2xl);
		font-weight: var(--fw-display);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		line-height: 1.1;
		background: var(--c-accent);
		color: var(--c-ink);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		padding: var(--space-1) var(--space-4);
	}

	.header-right {
		display: flex;
		justify-content: flex-end;
		flex: 1;
	}

	.overlay {
		position: fixed;
		inset: 0;
		background: var(--c-scrim);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 1000;
	}

	.modal {
		background: var(--c-bg);
		padding: var(--space-7) var(--space-8);
		text-align: center;
		border: var(--border-lg);
		box-shadow: var(--shadow-lg);
		animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	}

	.modal--win {
		background: var(--c-success);
	}

	.modal--lose {
		background: var(--c-danger);
		color: var(--c-on-danger);
	}

	.modal--draw {
		background: var(--c-accent);
	}

	@keyframes popIn {
		0% {
			transform: translate(6px, 6px);
			box-shadow: none;
		}
		100% {
			transform: translate(0, 0);
			box-shadow: var(--shadow-lg);
		}
	}

	.result-text {
		font-size: var(--fs-3xl);
		margin: 0;
		text-transform: uppercase;
	}

	.elo-text {
		font-family: var(--font-mono);
		font-size: var(--fs-lg);
		font-weight: var(--fw-bold);
		margin: var(--space-3) 0 var(--space-6);
	}

	.game {
		--canvas-side: 50vmin;
		--tool-size: calc(var(--canvas-side) * 0.1);
		--tool-gap: 0.5rem;
		--meter-bar-height: calc(var(--canvas-side) - var(--space-8));
		display: flex;
		justify-content: center;
		align-items: center;
		gap: var(--space-6);
		padding: var(--space-4);
	}

	canvas {
		width: var(--canvas-side);
		height: var(--canvas-side);
		background: var(--c-bg);
		border: var(--border-lg);
		box-shadow: var(--shadow);
		cursor: crosshair;
		touch-action: none;
	}

	.tools {
		display: grid;
		grid-template-columns: repeat(3, var(--tool-size));
		gap: var(--tool-gap);
	}

	.tools > * {
		width: var(--tool-size);
		height: var(--tool-size);
		margin: 0;
		padding: 0;
		border: var(--border);
		background: var(--c-bg);
		cursor: pointer;
		font-size: calc(var(--tool-size) * 0.25);
		line-height: 1;
		box-shadow: var(--shadow-sm);
		transition:
			transform var(--transition),
			box-shadow var(--transition);
	}

	.tools > *:hover:not(:disabled) {
		transform: translate(calc(-1 * var(--nudge)), calc(-1 * var(--nudge)));
		box-shadow: var(--shadow);
	}

	.tools > *:active:not(:disabled) {
		transform: translate(var(--press), var(--press));
		box-shadow: none;
	}

	.tools > *:disabled {
		opacity: 0.35;
		box-shadow: none;
		cursor: not-allowed;
	}

	.tools > .clear-btn {
		font-family: var(--font-mono);
		font-size: 10px;
		font-weight: var(--fw-bold);
		text-transform: uppercase;
	}

	.bars {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: var(--space-4);
		max-width: calc(var(--tool-size) * 6);
		max-height: var(--canvas-side);
		overflow-y: auto;
	}

	.meter {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-2);
	}

	.meter-value {
		font-family: var(--font-mono);
		font-size: var(--fs-lg);
		font-weight: var(--fw-bold);
		font-variant-numeric: tabular-nums;
	}

	.meter-label {
		font-family: var(--font-display);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		max-width: calc(var(--tool-size) * 1.6);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.meter-label--you {
		color: var(--c-primary);
	}

	.meter-label--opponent {
		color: var(--c-danger);
	}

	.loaderBar {
		width: var(--tool-size);
		height: var(--meter-bar-height);
		background: var(--c-bg-alt);
		border: var(--border);
		box-shadow: var(--shadow-sm);
		position: relative;
		overflow: hidden;
	}

	.loaderBar-fill {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		background: repeating-linear-gradient(
			45deg,
			var(--c-primary) 0 14px,
			var(--c-primary-dark) 14px 28px
		);
		transition: height 0.3s ease;
	}

	.loaderBar--opponent .loaderBar-fill {
		background: repeating-linear-gradient(
			45deg,
			var(--c-danger) 0 14px,
			var(--c-danger-dark) 14px 28px
		);
	}

	.meter.offline {
		opacity: 0.4;
		filter: grayscale(100%);
		transition: all 0.3s ease;
	}

	.meter.offline .loaderBar-fill {
		transition: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.timer.low {
			animation: none;
		}

		.modal {
			animation: none;
		}
	}

	@media (max-width: 760px) {
		.game-header {
			flex-direction: column;
			gap: var(--space-3);
			padding: var(--space-4);
		}

		.header-left,
		.header-center,
		.header-right {
			flex: none;
			justify-content: center;
		}

		.header-left {
			flex-wrap: wrap;
		}

		.game {
			--canvas-side: 78vmin;
			display: grid;
			grid-template-columns: auto auto;
			gap: var(--space-3) var(--space-4);
			padding: var(--space-3);
			justify-content: center;
			justify-items: center;
			align-items: center;
		}

		canvas {
			grid-column: 1 / -1;
			grid-row: 1;
		}

		.tools {
			grid-column: 1;
			grid-row: 2;
		}

		.bars {
			grid-column: 2;
			grid-row: 2;
		}

		.modal {
			padding: var(--space-6) var(--space-5);
			margin: var(--space-4);
		}
	}

	.cd-page {
		position: fixed;
		inset: 0;
		z-index: 900;
		display: grid;
		grid-template-rows: 28vh 1fr 18vh;
		background: var(--c-bg);
		overflow: hidden;
	}

	.cd-top {
		display: flex;
		flex-wrap: wrap;
		border-bottom: var(--border-lg);
	}

	.cd-half {
		flex: 1;
		min-width: 20%;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding: var(--space-5) var(--space-7);
		gap: var(--space-2);
		animation: cdHalfIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
	}

	.cd-you {
		animation-delay: 0s;
	}

	.cd-opp {
		align-items: flex-end;
		text-align: right;
		animation-delay: 0.06s;
	}

	@keyframes cdHalfIn {
		from {
			transform: translateY(-24px);
			opacity: 0;
		}
		to {
			transform: none;
			opacity: 1;
		}
	}

	.cd-tag {
		font-family: var(--font-mono);
		font-size: var(--fs-xs);
		font-weight: var(--fw-bold);
		text-transform: uppercase;
		letter-spacing: 0.22em;
		color: var(--c-muted);
	}

	.cd-pname {
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: clamp(1.6rem, 4.5vw, 3.5rem);
		text-transform: uppercase;
		line-height: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 42vw;
	}

	.cd-you .cd-pname {
		color: var(--c-primary);
	}

	.cd-opp .cd-pname {
		color: var(--c-danger);
	}

	.cd-pelo {
		font-family: var(--font-mono);
		font-weight: var(--fw-bold);
		font-size: var(--fs-xl);
		color: var(--c-ink);
	}

	.cd-pelo em {
		font-style: normal;
		font-size: var(--fs-xs);
		font-weight: var(--fw-regular);
		color: var(--c-muted);
		margin-left: var(--space-1);
		letter-spacing: 0.12em;
	}

	.cd-mid {
		display: flex;
		align-items: center;
		justify-content: center;
		border-bottom: var(--border-lg);
	}

	.cd-page[data-count='3'] .cd-mid {
		background: var(--c-accent);
	}

	.cd-page[data-count='2'] .cd-mid {
		background: var(--c-bg-alt);
	}

	.cd-page[data-count='1'] .cd-mid {
		background: var(--c-danger);
	}

	.cd-page[data-count='0'] .cd-mid {
		background: var(--c-success);
	}

	.cd-num {
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: min(48vh, 40vw);
		line-height: 1;
		color: var(--c-ink);
		user-select: none;
		pointer-events: none;
		animation: cdNumStamp 1s cubic-bezier(0.4, 0, 0.2, 1) both;
	}

	.cd-page[data-count='1'] .cd-num {
		color: #ffffff;
	}

	.cd-num.cd-go {
		font-size: min(22vh, 18vw);
		animation: cdGoBlast 0.65s cubic-bezier(0.4, 0, 0.2, 1) both;
	}

	@keyframes cdNumStamp {
		0% {
			transform: translateY(-22%) scaleY(1.18);
			opacity: 0;
		}
		16% {
			transform: translateY(2%) scaleY(0.88);
			opacity: 1;
		}
		26% {
			transform: translateY(0) scale(1);
			opacity: 1;
		}
		80% {
			transform: translateY(0) scale(1);
			opacity: 1;
		}
		100% {
			transform: translateY(6%) scaleY(0.94);
			opacity: 0;
		}
	}

	@keyframes cdGoBlast {
		0% {
			transform: scale(0.25);
			opacity: 0;
			letter-spacing: -0.12em;
		}
		38% {
			transform: scale(1.06);
			opacity: 1;
			letter-spacing: 0.04em;
		}
		62% {
			transform: scale(1);
			opacity: 1;
		}
		100% {
			transform: scale(1.18);
			opacity: 0;
		}
	}

	.cd-bot {
		background: var(--c-ink);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-5);
		padding: 0 var(--space-6);
		animation: cdBotIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) 0.1s both;
	}

	@keyframes cdBotIn {
		from {
			transform: translateY(24px);
			opacity: 0;
		}
		to {
			transform: none;
			opacity: 1;
		}
	}

	.cd-draw-tag {
		font-family: var(--font-mono);
		font-size: var(--fs-sm);
		font-weight: var(--fw-bold);
		letter-spacing: 0.28em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.4);
	}

	.cd-draw-word {
		font-family: var(--font-display);
		font-weight: var(--fw-display);
		font-size: clamp(2rem, 5vw, 4rem);
		text-transform: uppercase;
		letter-spacing: 0.03em;
		color: var(--c-accent);
	}

	@media (max-width: 640px) {
		.cd-page {
			grid-template-rows: 32vh 1fr 16vh;
		}

		.cd-half {
			padding: var(--space-4);
		}

		.cd-pname {
			font-size: clamp(1.1rem, 5.5vw, 2rem);
		}

		.cd-num {
			font-size: min(42vh, 54vw);
		}

		.cd-num.cd-go {
			font-size: min(20vh, 30vw);
		}

		.cd-draw-word {
			font-size: clamp(1.4rem, 7vw, 2.2rem);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.cd-half,
		.cd-bot,
		.cd-num {
			animation: none;
		}
	}
</style>
