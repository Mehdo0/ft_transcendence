<script lang="ts">
	import { untrack } from 'svelte';
	import type { ReplayEvent, ReplayPoint, ReplayStroke } from '$lib/game/roundResult';

	let {
		events,
		playbackDuration,
		timelineDuration,
		lineColor = '#0a0a0a',
		lineWidth = 3,
		onscorechange = undefined
	}: {
		events: ReplayEvent[];
		playbackDuration: number;
		timelineDuration: number;
		lineColor?: string;
		lineWidth?: number;
		onscorechange?: (score: number) => void;
	} = $props();

	let canvas: HTMLCanvasElement;
	let context: CanvasRenderingContext2D | null = null;
	let animationFrame: number | null = null;
	let eventIndex = 0;
	let drawing: ReplayStroke[] = [];
	let score = 0;
	let orderedEvents = $derived([...events].sort((left, right) => left.elapsed - right.elapsed));

	function clonePoints(points: ReplayPoint[]): ReplayPoint[] {
		return points.map((point) => ({ ...point }));
	}

	function cloneStrokes(strokes: ReplayStroke[]): ReplayStroke[] {
		return strokes.map((stroke) => ({ points: clonePoints(stroke.points) }));
	}

	function canvasPoint(point: ReplayPoint): ReplayPoint {
		return {
			x: point.x * canvas.clientWidth,
			y: point.y * canvas.clientHeight
		};
	}

	function drawDot(point: ReplayPoint): void {
		if (!context) return;
		const position = canvasPoint(point);
		context.beginPath();
		context.arc(position.x, position.y, lineWidth / 2, 0, Math.PI * 2);
		context.fill();
	}

	function drawStroke(stroke: ReplayStroke): void {
		if (!context || stroke.points.length === 0) return;
		if (stroke.points.length === 1) {
			drawDot(stroke.points[0]);
			return;
		}
		const start = canvasPoint(stroke.points[0]);
		context.beginPath();
		context.moveTo(start.x, start.y);
		for (let index = 1; index < stroke.points.length; index += 1) {
			const point = canvasPoint(stroke.points[index]);
			context.lineTo(point.x, point.y);
		}
		context.stroke();
	}

	function draw(): void {
		if (!context) return;
		context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
		context.strokeStyle = lineColor;
		context.fillStyle = lineColor;
		context.lineWidth = lineWidth;
		context.lineCap = 'round';
		context.lineJoin = 'round';
		for (const stroke of drawing) drawStroke(stroke);
	}

	function updateScore(value: number): void {
		if (score === value) return;
		score = value;
		onscorechange?.(score);
	}

	function applyEvent(event: ReplayEvent): boolean {
		updateScore(event.score);
		switch (event.action) {
			case 'append_stroke':
				drawing = [...drawing, { points: clonePoints(event.points) }];
				return true;
			case 'append_points': {
				const lastStroke = drawing.at(-1);
				if (!lastStroke) return false;
				lastStroke.points.push(...clonePoints(event.points));
				return true;
			}
			case 'remove_stroke':
				drawing = drawing.slice(0, -1);
				return true;
			case 'clear':
				drawing = [];
				return true;
			case 'replace':
				drawing = cloneStrokes(event.strokes);
				return true;
			case 'score':
				return false;
		}
	}

	function advance(targetElapsed: number): void {
		let drawingChanged = false;
		while (
			eventIndex < orderedEvents.length &&
			orderedEvents[eventIndex].elapsed <= targetElapsed
		) {
			drawingChanged = applyEvent(orderedEvents[eventIndex]) || drawingChanged;
			eventIndex += 1;
		}
		if (drawingChanged) draw();
	}

	function resize(): void {
		if (!context) return;
		const ratio = window.devicePixelRatio || 1;
		const width = Math.max(1, Math.floor(canvas.clientWidth));
		const height = Math.max(1, Math.floor(canvas.clientHeight));
		canvas.width = Math.floor(width * ratio);
		canvas.height = Math.floor(height * ratio);
		context.setTransform(ratio, 0, 0, ratio, 0, 0);
		draw();
	}

	function animate(startedAt: number, timestamp: number): void {
		const durationMs = Math.max(1, playbackDuration * 1000);
		const progress = Math.min(1, (timestamp - startedAt) / durationMs);
		advance(timelineDuration * progress);
		if (progress < 1) {
			animationFrame = requestAnimationFrame((nextTimestamp) => animate(startedAt, nextTimestamp));
		}
	}

	$effect(() => {
		return untrack(() => {
			context = canvas.getContext('2d');
			const observer = new ResizeObserver(resize);
			observer.observe(canvas);
			resize();
			onscorechange?.(score);

			if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
				advance(Number.POSITIVE_INFINITY);
			} else {
				animationFrame = requestAnimationFrame((timestamp) => animate(timestamp, timestamp));
			}

			return () => {
				observer.disconnect();
				if (animationFrame !== null) cancelAnimationFrame(animationFrame);
			};
		});
	});
</script>

<canvas
	bind:this={canvas}
	class="aspect-square w-full border-4 border-ink bg-bg"
	aria-label="Drawing replay"
></canvas>
