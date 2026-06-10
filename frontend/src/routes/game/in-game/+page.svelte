<script lang="ts">
	import { getWs, setWs } from '$lib/stores/ws';
	import { game } from '$lib/stores/game.svelte';
	import favicon from '$lib/draw_meter_logo.svg';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	type Point = { x: number; y: number };
	type Trait = { color: string; width: number; points: Point[] };

	let canvas: HTMLCanvasElement = $state()!;
	let ratio = $state(1);
	let context: CanvasRenderingContext2D = $state()!;
	let last = $state<Point | null>(null);
	let selectedColor = $state('#000000');
	let lastSelectedColor = $state('#000000');
	let stack = $state<Trait[]>([]);
	let redoStack = $state<Trait[]>([]);

	let lineWidth = $state(1);
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

	const GUESS_EVERY_POINTS = 10;

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

	const COLORS = [
		'#ff0000',
		'#00ff00',
		'#0000ff',
		'#ffff00',
		'#00ffff',
		'#ff00ff',
		'#000000',
		'#808080',
		'#ff8000'
	];
	function clearSessionData() {
		sessionStorage.removeItem('draw_stack');
		sessionStorage.removeItem('draw_my_score');
		sessionStorage.removeItem('draw_opp_score');
		sessionStorage.removeItem('draw_word');
		sessionStorage.removeItem('draw_opponent');
		sessionStorage.removeItem('draw_ends_at');
	}

	onMount(() => {
		const savedStack = sessionStorage.getItem('draw_stack');
		if (savedStack) stack = JSON.parse(savedStack);

		const savedOppScore = sessionStorage.getItem('draw_opp_score');
		if (savedOppScore) game.opponent_score = parseFloat(savedOppScore);

		const isReconnect = !!sessionStorage.getItem('draw_word');

		const savedWord = sessionStorage.getItem('draw_word');
		if (savedWord) game.word = savedWord;

		const savedOpponent = sessionStorage.getItem('draw_opponent');
		if (savedOpponent) game.opponent = savedOpponent;

		const savedEndsAt = sessionStorage.getItem('draw_ends_at');
		endsAt = savedEndsAt ? parseInt(savedEndsAt) : Date.now() + 63000;
		startTimer();

		if (!isReconnect) {
			showCountdown = true;
			fetch('/api/users/me/', { credentials: 'same-origin' })
				.then((r) => (r.ok ? r.json() : null))
				.then((d) => { if (d) { myUsername = d.username; myElo = d.elo; } })
				.catch(() => {});
			fetch(`/api/users/${game.opponent}/stats`, { credentials: 'same-origin' })
				.then((r) => (r.ok ? r.json() : null))
				.then((d) => { if (d) opponentElo = d.Elo; })
				.catch(() => {});
			setTimeout(() => { countdownNum = 2; }, 1000);
			setTimeout(() => { countdownNum = 1; }, 2000);
			setTimeout(() => { countdownNum = 0; }, 3000);
			setTimeout(() => { showCountdown = false; }, 3600);
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
					game.my_score = msg.guess[game.word];
					sessionStorage.setItem('draw_my_score', game.my_score.toString());
					break;
				case 'reconnect_game':
					game.id = msg.game_id;
					game.opponent = msg.opponent;
					game.word = msg.word;
					sessionStorage.setItem('draw_word', game.word);
					sessionStorage.setItem('draw_opponent', game.opponent);
					if (msg.time_left != null) {
						endsAt = Date.now() + msg.time_left * 1000;
						sessionStorage.setItem('draw_ends_at', String(endsAt));
						startTimer();
					}
					break;
				case 'opponent_guess':
					game.opponent_score = msg.guess[game.word];
					sessionStorage.setItem('draw_opp_score', game.opponent_score.toString());
					break;
				case 'end_game':
					stopTimer();
					elo_diff = msg.elo_diff;
					result = msg.status;
					clearSessionData();
					break;
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
		const dpr = window.devicePixelRatio || 1;
		canvas.width = canvas.clientWidth * dpr;
		canvas.height = canvas.clientHeight * dpr;
		ratio = canvas.width;
		context.scale(dpr, dpr);
		redraw();
	}

	function redraw() {
		context.clearRect(0, 0, canvas.width, canvas.height);

		for (const trait of stack) {
			if (trait.points.length === 0) continue;

			context.strokeStyle = trait.color;
			context.lineWidth = trait.width * canvas.clientWidth;
			context.lineCap = 'round';
			context.lineJoin = 'round';
			context.beginPath();
			context.moveTo(trait.points[0].x * ratio, trait.points[0].y * ratio);
			for (let i = 1; i < trait.points.length; i++) {
				context.lineTo(trait.points[i].x * ratio, trait.points[i].y * ratio);
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

	function eraser() {
		selectedColor = '#ffffff';
	}

	function pencil() {
		selectedColor = lastSelectedColor;
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
</script>

<svelte:window onresize={resize} />

{#if showCountdown}
	<div class="cd-page" data-count={countdownNum} aria-live="assertive" aria-atomic="true">
		<div class="cd-top">
			<div class="cd-half cd-you">
				<span class="cd-tag">Player 01</span>
				<span class="cd-pname">{myUsername || 'You'}</span>
				<span class="cd-pelo">{myElo !== null ? myElo : '—'}<em>ELO</em></span>
			</div>
			<div class="cd-separator"></div>
			<div class="cd-half cd-opp">
				<span class="cd-tag">Player 02</span>
				<span class="cd-pname">{game.opponent}</span>
				<span class="cd-pelo">{opponentElo !== null ? opponentElo : '—'}<em>ELO</em></span>
			</div>
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
		<div class="vs-badge">
			VS <strong>{game.opponent}</strong>
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
		<button class="nb-btn nb-btn--danger" onclick={surrender}> Surrender ⚑ </button>
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
				<p class="elo-text positive">+{elo_diff} Elo</p>
			{:else if result === 'draw'}
				<h2 class="result-text">Draw</h2>
				<p class="elo-text">No Elo change</p>
			{:else}
				<h2 class="result-text">You Lost</h2>
				<p class="elo-text negative">{elo_diff} Elo</p>
			{/if}
			<button class="nb-btn nb-btn--primary" onclick={() => goto('/')}>Back to Home</button>
		</div>
	</div>
{/if}

<div class="game">
	<div class="tools">
		{#each COLORS as c (c)}
			<button
				class="swatch"
				style="background:{c}"
				title={c}
				onclick={() => {
					selectedColor = c;
					lastSelectedColor = c;
				}}
				aria-label={c}
			></button>
		{/each}
		<button
			class:active={selectedColor !== '#ffffff'}
			onclick={pencil}
			aria-label="Pencil"
			title="Pencil">✏️</button
		>
		<input
			type="color"
			bind:value={selectedColor}
			oninput={() => (lastSelectedColor = selectedColor)}
			aria-label="Pick a color"
			title="Pick a color"
		/>
		<button
			class:active={selectedColor === '#ffffff'}
			onclick={eraser}
			aria-label="Eraser"
			title="Eraser">🧹</button
		>
		<input
			class="width"
			type="range"
			min="1"
			max="20"
			step="0.5"
			bind:value={lineWidth}
			aria-label="Brush size"
			title="Brush size"
		/>
		<button onclick={undo} disabled={stack.length === 0} aria-label="Undo" title="Undo">↶</button>
		<button onclick={redo} disabled={redoStack.length === 0} aria-label="Redo" title="Redo"
			>↷</button
		>
	</div>

	<canvas
		bind:this={canvas}
		onpointerdown={(e) => {
			stack.push({
				color: selectedColor,
				width: lineWidth / 100,
				points: [{ x: e.offsetX / ratio, y: e.offsetY / ratio }]
			});

			redoStack = [];
			last = { x: e.offsetX / ratio, y: e.offsetY / ratio };
		}}
		onpointerup={finishStroke}
		onpointerleave={finishStroke}
		onpointermove={(e) => {
			if (e.buttons !== 1 || !last) return;

			context.strokeStyle = selectedColor;
			context.lineWidth = stack[stack.length - 1].width * canvas.clientWidth;
			context.lineCap = 'round';
			context.lineJoin = 'round';
			context.beginPath();
			context.moveTo(last.x * ratio, last.y * ratio);
			context.lineTo(e.offsetX * ratio, e.offsetY * ratio);
			context.stroke();

			stack[stack.length - 1].points.push({ x: e.offsetX / ratio, y: e.offsetY / ratio });
			last = { x: e.offsetX / ratio, y: e.offsetY / ratio };
			pointsSinceLastGuess += 1;

			if (pointsSinceLastGuess >= GUESS_EVERY_POINTS) {
				pointsSinceLastGuess = 0;
				makeAiGuess();
			}
		}}
	></canvas>

	<div class="bars">
		<div class="meter">
			<span class="meter-value">{Math.round(game.my_score ?? 0)}%</span>
			<div class="loaderBar">
				<div class="loaderBar-fill" style="height: {game.my_score ?? 0}%"></div>
			</div>
			<span class="meter-label meter-label--you">You</span>
		</div>
		<div class="meter">
			<span class="meter-value">{Math.round(game.opponent_score ?? 0)}%</span>
			<div class="loaderBar loaderBar--opponent">
				<div class="loaderBar-fill" style="height: {game.opponent_score ?? 0}%"></div>
			</div>
			<span class="meter-label meter-label--opponent">{game.opponent || 'Rival'}</span>
		</div>
	</div>
</div>

<style>
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
		font-size: calc(var(--tool-size) * 0.5);
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

	.tools > .active {
		background: var(--c-accent);
		box-shadow: none;
		transform: translate(var(--press), var(--press));
	}

	.tools > *:disabled {
		opacity: 0.35;
		box-shadow: none;
		cursor: not-allowed;
	}

	.tools > .swatch {
		font-size: 0;
	}

	.tools > input[type='color'] {
		padding: 2px;
	}

	.tools > .width {
		grid-column: 1 / -1;
		width: 100%;
		height: auto;
		box-shadow: none;
		background: transparent;
		border: none;
		accent-color: var(--c-primary);
	}

	.tools > .width:hover:not(:disabled) {
		transform: none;
	}

	.bars {
		display: flex;
		gap: var(--space-4);
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
		height: var(--canvas-side);
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

	/* ── Countdown full-page ──────────────────────────────── */

	.cd-page {
		position: fixed;
		inset: 0;
		z-index: 900;
		display: grid;
		grid-template-rows: 28vh 1fr 18vh;
		background: var(--c-bg);
		overflow: hidden;
	}

	/* TOP — player duel */
	.cd-top {
		display: flex;
		border-bottom: var(--border-lg);
	}

	.cd-half {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding: var(--space-5) var(--space-7);
		gap: var(--space-2);
		animation: cdHalfIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
	}

	.cd-you { animation-delay: 0s; }

	.cd-opp {
		align-items: flex-end;
		text-align: right;
		animation-delay: 0.06s;
	}

	@keyframes cdHalfIn {
		from { transform: translateY(-24px); opacity: 0; }
		to   { transform: none; opacity: 1; }
	}

	.cd-separator {
		width: var(--border-w-lg);
		background: var(--c-ink);
		flex-shrink: 0;
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

	.cd-you .cd-pname { color: var(--c-primary); }
	.cd-opp .cd-pname { color: var(--c-danger); }

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

	/* MIDDLE — the number, full width, color shifts per count */
	.cd-mid {
		display: flex;
		align-items: center;
		justify-content: center;
		border-bottom: var(--border-lg);
	}

	.cd-page[data-count="3"] .cd-mid { background: var(--c-accent); }
	.cd-page[data-count="2"] .cd-mid { background: var(--c-bg-alt); }
	.cd-page[data-count="1"] .cd-mid { background: var(--c-danger); }
	.cd-page[data-count="0"] .cd-mid { background: var(--c-success); }

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

	.cd-page[data-count="1"] .cd-num { color: #ffffff; }

	.cd-num.cd-go {
		font-size: min(22vh, 18vw);
		animation: cdGoBlast 0.65s cubic-bezier(0.4, 0, 0.2, 1) both;
	}

	@keyframes cdNumStamp {
		0%   { transform: translateY(-22%) scaleY(1.18); opacity: 0; }
		16%  { transform: translateY(2%) scaleY(0.88); opacity: 1; }
		26%  { transform: translateY(0) scale(1); opacity: 1; }
		80%  { transform: translateY(0) scale(1); opacity: 1; }
		100% { transform: translateY(6%) scaleY(0.94); opacity: 0; }
	}

	@keyframes cdGoBlast {
		0%   { transform: scale(0.25); opacity: 0; letter-spacing: -0.12em; }
		38%  { transform: scale(1.06); opacity: 1; letter-spacing: 0.04em; }
		62%  { transform: scale(1); opacity: 1; }
		100% { transform: scale(1.18); opacity: 0; }
	}

	/* BOTTOM — the word */
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
		from { transform: translateY(24px); opacity: 0; }
		to   { transform: none; opacity: 1; }
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
