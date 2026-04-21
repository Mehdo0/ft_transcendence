<script>
	let { color, size } = $props();

	let canvas = $state();
	let context = $state();
	let coords = $state();

	$effect(() => {
		context = canvas.getContext('2d');
		resize();
	});

	function resize() {
		const dpr = window.devicePixaelRatio || 1;

		canvas.width = window.innerWidth * dpr;
		canvas.height = window.innerHeight * dpr;

		canvas.style.width = window.innerWidth + 'px';
		canvas.style.height = window.innerHeight + 'px';

		context.scale(dpr, dpr);
	}
</script>

<svelte:window onresize={resize} />

<div class="square">

	<canvas
		bind:this={canvas}
		onpointerdown={(e) => {
			coords = { x: e.offsetX, y: e.offsetY };

			context.fillStyle = color;
			context.beginPath();
			context.arc(coords.x, coords.y, size / 2, 0, 2 * Math.PI);
			context.fill();
		}}
		onpointerleave={() => {
			coords = null;
		}}
		onpointermove={(e) => {
			const previous = coords;

			coords = { x: e.offsetX, y: e.offsetY };

			if (e.buttons === 1) {
				e.preventDefault();

				context.strokeStyle = color;
				context.lineWidth = size;
				context.lineCap = 'round';
				context.beginPath();
				context.moveTo(previous.x, previous.y);
				context.lineTo(coords.x, coords.y);
				context.stroke();
			}
		}}
	></canvas>
</div>
{#if coords}
	<div
		class="preview"
		style="--color: {color}; --size: {size}px; --x: {coords.x}px; --y: {coords.y}px"
	></div>
{/if}

<style>
	.square {
		width: 90vw;
		aspect-ratio: 1;
		box-sizing: border-box;
		border: 2px solid black;
		position: relative;

	}
	canvas {
		position: absolute;
		left: 0;
		top: 0;
		width: 100%;
		height: 100%;
	}

	.preview {
		position: absolute;
		left: var(--x);
		top: var(--y);
		width: var(--size);
		height: var(--size);
		transform: translate(-50%, -50%);
		background: var(--color);
		border-radius: 50%;
		opacity: 0.5;
		pointer-events: none;
	}
</style>
