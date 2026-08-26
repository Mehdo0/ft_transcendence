export type ReplayPoint = {
	x: number;
	y: number;
};

export type ReplayStroke = {
	points: ReplayPoint[];
};

export type ReplayAction =
	| 'append_stroke'
	| 'append_points'
	| 'remove_stroke'
	| 'clear'
	| 'replace'
	| 'score';

export type ReplayEvent = {
	elapsed: number;
	score: number;
	action: ReplayAction;
	points: ReplayPoint[];
	strokes: ReplayStroke[];
};

export type RoundResult = {
	round_number: number;
	winner: string | null;
	is_tie: boolean;
	match_complete: boolean;
	duration: number;
	final_hold_duration: number;
	timeline_duration: number;
	drawings: Record<string, ReplayStroke[]>;
	timelines: Record<string, ReplayEvent[]>;
	scores: Record<string, number>;
	round_wins: Record<string, number>;
};

const REPLAY_ACTIONS = new Set<ReplayAction>([
	'append_stroke',
	'append_points',
	'remove_stroke',
	'clear',
	'replace',
	'score'
]);

function asRecord(value: unknown): Record<string, unknown> | null {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
	return value as Record<string, unknown>;
}

function parseNumberRecord(value: unknown): Record<string, number> {
	const record = asRecord(value);
	if (!record) return {};

	return Object.fromEntries(
		Object.entries(record).flatMap(([key, item]) =>
			typeof item === 'number' && Number.isFinite(item) ? [[key, item]] : []
		)
	);
}

function parsePoint(value: unknown): ReplayPoint | null {
	const point = asRecord(value);
	if (!point || typeof point.x !== 'number' || typeof point.y !== 'number') return null;
	if (!Number.isFinite(point.x) || !Number.isFinite(point.y)) return null;
	return { x: point.x, y: point.y };
}

function parseStrokes(value: unknown): ReplayStroke[] {
	if (!Array.isArray(value)) return [];

	return value.flatMap((item) => {
		const stroke = asRecord(item);
		if (!stroke || !Array.isArray(stroke.points)) return [];
		const points = stroke.points.flatMap((point) => {
			const parsedPoint = parsePoint(point);
			return parsedPoint ? [parsedPoint] : [];
		});
		return points.length > 0 ? [{ points }] : [];
	});
}

function parseDrawings(value: unknown): Record<string, ReplayStroke[]> {
	const drawings = asRecord(value);
	if (!drawings) return {};
	return Object.fromEntries(
		Object.entries(drawings).map(([username, strokes]) => [username, parseStrokes(strokes)])
	);
}

function parseReplayEvent(value: unknown): ReplayEvent | null {
	const event = asRecord(value);
	if (!event) return null;
	if (typeof event.elapsed !== 'number' || !Number.isFinite(event.elapsed)) return null;
	if (typeof event.score !== 'number' || !Number.isFinite(event.score)) return null;
	if (typeof event.action !== 'string' || !REPLAY_ACTIONS.has(event.action as ReplayAction)) {
		return null;
	}
	return {
		elapsed: Math.max(0, event.elapsed),
		score: event.score,
		action: event.action as ReplayAction,
		points: Array.isArray(event.points)
			? event.points.flatMap((point) => {
					const parsedPoint = parsePoint(point);
					return parsedPoint ? [parsedPoint] : [];
				})
			: [],
		strokes: parseStrokes(event.strokes)
	};
}

function parseTimelines(value: unknown): Record<string, ReplayEvent[]> {
	const timelines = asRecord(value);
	if (!timelines) return {};
	return Object.fromEntries(
		Object.entries(timelines).map(([username, events]) => [
			username,
			Array.isArray(events)
				? events.flatMap((event) => {
						const parsedEvent = parseReplayEvent(event);
						return parsedEvent ? [parsedEvent] : [];
					})
				: []
		])
	);
}

export function parseRoundResult(value: unknown): RoundResult | null {
	const result = asRecord(value);
	if (!result) return null;

	const roundNumber = result.round_number;
	const duration = result.duration;
	const finalHoldDuration = result.final_hold_duration;
	const timelineDuration = result.timeline_duration;
	if (typeof roundNumber !== 'number' || !Number.isInteger(roundNumber) || roundNumber < 1) {
		return null;
	}
	if (typeof duration !== 'number' || !Number.isFinite(duration) || duration <= 0) return null;
	if (
		typeof finalHoldDuration !== 'number' ||
		!Number.isFinite(finalHoldDuration) ||
		finalHoldDuration <= 0 ||
		finalHoldDuration >= duration
	) {
		return null;
	}
	if (
		typeof timelineDuration !== 'number' ||
		!Number.isFinite(timelineDuration) ||
		timelineDuration < 0
	) {
		return null;
	}

	return {
		round_number: roundNumber,
		winner: typeof result.winner === 'string' ? result.winner : null,
		is_tie: result.is_tie === true,
		match_complete: result.match_complete === true,
		duration,
		final_hold_duration: finalHoldDuration,
		timeline_duration: timelineDuration,
		drawings: parseDrawings(result.drawings),
		timelines: parseTimelines(result.timelines),
		scores: parseNumberRecord(result.scores),
		round_wins: parseNumberRecord(result.round_wins)
	};
}
