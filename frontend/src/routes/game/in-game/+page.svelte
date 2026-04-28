<script lang="ts">
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

	$effect(() => {
		context = canvas.getContext('2d')!;
		resize();
	});

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
	}

	function redo() {
		const trait = redoStack.pop();
		if (!trait) return;
		stack.push(trait);
		redraw();
	}
	function eraser() {
		selectedColor = '#ffffff';
	}
	function pencil() {
		selectedColor = lastSelectedColor;
	}
</script>

<svelte:window onresize={resize} />
<h1>Draw !</h1>

<div class="arena">
	<div class="you">
		<p>You</p>
		<div class="canvas-row">
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
				onpointerup={() => (last = null)}
				onpointerleave={() => (last = null)}
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
				}}
			></canvas>
			<div class="loaderBar"></div>
			<div class="loaderBar loaderBar--opponent"></div>
		</div>
		<div class="tools">
			<label>
				Color
				<input
					type="color"
					bind:value={selectedColor}
					oninput={() => (lastSelectedColor = selectedColor)}
				/>
			</label>
			<label>
				Width
				<input type="range" min="1" max="20" step="0.5" bind:value={lineWidth} />
			</label>
			<button onclick={pencil}>✏️</button>
			<button onclick={eraser}>🧹</button>
			<button onclick={undo}>↶</button>
			<button onclick={redo}>↷</button>

			{#each COLORS as c}
				<button
					title={c}
					style="color:{c}"
					onclick={() => {
						selectedColor = c;
						lastSelectedColor = c;
					}}>●</button
				>
			{/each}
		</div>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: system-ui, sans-serif;
		background: #f4f5f7;
		color: #1f2937;
	}

	h1 {
		text-align: center;
		margin: 1.5rem 0 0.5rem;
		font-weight: 600;
		letter-spacing: 0.02em;
	}

	label {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	input[type='color'] {
		width: 2.25rem;
		height: 2.25rem;
		border: none;
		border-radius: 50%;
		cursor: pointer;
		background: transparent;
	}

	canvas {
		width: var(--canvas-side);
		height: var(--canvas-side);
		background: #ffffff;
		border: 1px solid #d1d5db;
		border-radius: 12px;
	}

	p {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		font-weight: 500;
		color: #6b7280;
		margin: 0;
	}

	.arena {
		--canvas-side: 50vmin;
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		align-items: flex-start;
		gap: 2rem;
		padding: 1rem;
	}

	.you {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
	}

	.canvas-row {
		display: flex;
		align-items: stretch;
		gap: 0.5rem;
	}

	.tools {
		width: var(--canvas-side);
		max-width: 100%;
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		justify-content: center;
		align-items: center;
		gap: 0.5rem 0.75rem;
		box-sizing: border-box;
	}

	.loaderBar {
		width: calc(var(--canvas-side) * 0.1);
		height: var(--canvas-side);
		background: #f9f9f9;
		border-radius: 10px;
		border: 1px solid #006dfe;
		position: relative;
		overflow: hidden;
	}

	.loaderBar::before {
		content: '';
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		height: 0%;
		border-radius: 5px;
		background: repeating-linear-gradient(45deg, #0031f2 0 30px, #006dfe 0 40px);
		background-size: 200% 200%;
		background-position: center bottom;
		animation:
			fillProgress 6s ease-in-out infinite,
			lightEffect 1s infinite linear;
		animation-fill-mode: forwards;
	}

	@keyframes fillProgress {
		0% {
			height: 0%;
		}

		33% {
			height: 33.333%;
		}

		66% {
			height: 66.67%;
		}

		100% {
			height: 100%;
		}
	}

	@keyframes lightEffect {
		0%,
		20%,
		40%,
		60%,
		80%,
		100% {
			background: repeating-linear-gradient(45deg, #0031f2 0 30px, #006dfe 0 40px);
			background-size: 200% 200%;
			background-position: center bottom;
		}

		10%,
		30%,
		50%,
		70%,
		90% {
			background: repeating-linear-gradient(
					45deg,
					#0031f2 0 30px,
					#006dfe 0 40px,
					rgba(255, 255, 255, 0.3) 0 40px
				);
			background-size: 200% 200%;
			background-position: center bottom;
		}
	}

	.loaderBar--opponent {
		background: #fef2f2;
		border-color: #dc2626;
	}

	.loaderBar--opponent::before {
		background: repeating-linear-gradient(45deg, #991b1b 0 30px, #dc2626 0 40px);
		background-size: 200% 200%;
		background-position: center bottom;
		animation:
			fillProgress 6s ease-in-out infinite,
			lightEffectOpponent 1s infinite linear;
		animation-fill-mode: forwards;
	}

	@keyframes lightEffectOpponent {
		0%,
		20%,
		40%,
		60%,
		80%,
		100% {
			background: repeating-linear-gradient(45deg, #991b1b 0 30px, #dc2626 0 40px);
			background-size: 200% 200%;
			background-position: center bottom;
		}

		10%,
		30%,
		50%,
		70%,
		90% {
			background: repeating-linear-gradient(
					45deg,
					#991b1b 0 30px,
					#dc2626 0 40px,
					rgba(255, 255, 255, 0.35) 0 40px
				);
			background-size: 200% 200%;
			background-position: center bottom;
		}
	}
</style>
