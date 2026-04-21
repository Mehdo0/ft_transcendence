<script>
	let canvas = $state();
	let context = $state();
	let last = $state(/** @type {{x:number,y:number}|null} */ (null));
	let selectedColor = $state('#000000');

	$effect(() => {
		context = canvas.getContext('2d');
		resize();
	});

	function resize() {
		const dpr = window.devicePixelRatio || 1;

		canvas.width = canvas.clientWidth * dpr;
		canvas.height = canvas.clientHeight * dpr;

		context.scale(dpr, dpr);
	}
</script>

<svelte:window onresize={resize} />
<h1>Draw !</h1>
<label>
	Select a color 
	<input type="color" bind:value={selectedColor} />

</label>

<div>
	<label>
		You
	<canvas
		bind:this={canvas}
		onpointerdown={(e) => {
			last = { x: e.offsetX, y: e.offsetY };
		}}
		onpointerup={() => (last = null)}
		onpointerleave={() => (last = null)}
		onpointermove={(e) => {
			if (e.buttons !== 1 || !last) return;

			context.strokeStyle = selectedColor;
			context.lineWidth = 2;
			context.lineCap = 'round';
			context.beginPath();
			context.moveTo(last.x, last.y);
			context.lineTo(e.offsetX, e.offsetY);
			context.stroke();

			last = { x: e.offsetX, y: e.offsetY };
		}}
	></canvas>
	</label>
	<label>Opponent
		<canvas></canvas>
	</label>
</div>

<style>
	canvas {
		width: 50vmin;
		height: 50vmin;
		border: 2px solid black;
	}
	div {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		align-items:  center;
		min-height: 100vh;
		gap: 1rem;
	}
</style>
