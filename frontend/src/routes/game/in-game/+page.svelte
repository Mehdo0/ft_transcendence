<script lang="ts">
	type Point = { x: number; y: number };
	type Trait = { color: string; points: Point[] };

	let canvas: HTMLCanvasElement = $state()!;
	let context: CanvasRenderingContext2D = $state()!;
	let last = $state<Point | null>(null);
	let selectedColor = $state('#000000');

	let stack = $state<Trait[]>([]);
	let redoStack = $state<Trait[]>([]);

	let lineWidth = $state(2);

	$effect(() => {
		context = canvas.getContext('2d')!;
		resize();
	});

	function resize() {
		const dpr = window.devicePixelRatio || 1;

		canvas.width = canvas.clientWidth * dpr;
		canvas.height = canvas.clientHeight * dpr;

		context.scale(dpr, dpr);
	}

	function redraw() {
		context.clearRect(0, 0, canvas.width, canvas.height);

		for (const trait of stack) {
			if (trait.points.length === 0) continue;

			context.strokeStyle = trait.color;
			context.lineWidth = 2;
			context.lineCap = 'round';
			context.beginPath();
			context.moveTo(trait.points[0].x, trait.points[0].y);
			for (let i = 1; i < trait.points.length; i++) {
				context.lineTo(trait.points[i].x, trait.points[i].y);
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
		selectedColor = '#fff';
	}
	function modifyLineWidth(value: number) {
		lineWidth = value;
	}
</script>

<svelte:window onresize={resize} />
<h1>Draw !</h1>

<div class="arena">
	<div class="you">
		<p>You</p>
		<canvas
			bind:this={canvas}
			onpointerdown={(e) => {
				stack.push({ color: selectedColor, points: [{ x: e.offsetX, y: e.offsetY }] });
				redoStack = [];
				last = { x: e.offsetX, y: e.offsetY };
			}}
			onpointerup={() => (last = null)}
			onpointerleave={() => (last = null)}
			onpointermove={(e) => {
				if (e.buttons !== 1 || !last) return;

				context.strokeStyle = selectedColor;
				context.lineWidth = lineWidth;
				context.lineCap = 'round';
				context.beginPath();
				context.moveTo(last.x, last.y);
				context.lineTo(e.offsetX, e.offsetY);
				context.stroke();

				stack[stack.length - 1].points.push({ x: e.offsetX, y: e.offsetY });
				last = { x: e.offsetX, y: e.offsetY };
			}}
		></canvas>
		<div class="tools">
			<label>
				Color
				<input type="color" bind:value={selectedColor} />
			</label>
			<label>
				Width
				<input type="range" min="2" max="20" bind:value={lineWidth} />
			</label>
			<button onclick={eraser}>🧹</button>
			<button onclick={undo}>↶</button>
			<button onclick={redo}>↷</button>
		</div>
	</div>
	<p>
		Opponent
		<canvas></canvas>
	</p>
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
		width: 50vmin;
		height: 50vmin;
		background: #fff;
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

	.tools {
		width: 50vmin;
		max-width: 100%;
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		justify-content: center;
		align-items: center;
		gap: 0.5rem 0.75rem;
		box-sizing: border-box;
	}

	.tools label {
		margin-bottom: 0;
	}
</style>
