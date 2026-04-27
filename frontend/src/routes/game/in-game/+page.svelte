<script lang="ts">
	type Point = { x: number; y: number };
	type Trait = { color: string; width: number; points: Point[] };

	let canvas: HTMLCanvasElement = $state()!;
	let ratio = $state(1);
	let context: CanvasRenderingContext2D = $state()!;
	let last = $state<Point | null>(null);
	let selectedColor = $state('#000000');
	let stack = $state<Trait[]>([]);
	let redoStack = $state<Trait[]>([]);

	let lineWidth = $state(1);

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
		selectedColor = '#fff';
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
		<div class="tools">
			<label>
				Color
				<input type="color" bind:value={selectedColor} />
			</label>
			<label>
				Width
				<input type="range" min="1" max="20" step="0.5" bind:value={lineWidth} />
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
