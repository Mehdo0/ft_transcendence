const ROUND_END_KEY = 'draw_ends_at';
const COUNTDOWN_END_KEY = 'draw_countdown_ends_at';

export type RoundTiming = {
	roundEndsAt: number;
	countdownEndsAt: number;
};

function readTimestamp(key: string): number | null {
	const value = Number(sessionStorage.getItem(key));
	return Number.isFinite(value) && value > 0 ? value : null;
}

export function saveRoundTiming(totalSeconds: number, countdownSeconds: number): RoundTiming {
	const now = Date.now();
	const timing = {
		roundEndsAt: now + Math.max(0, totalSeconds) * 1000,
		countdownEndsAt: now + Math.max(0, countdownSeconds) * 1000
	};
	sessionStorage.setItem(ROUND_END_KEY, String(timing.roundEndsAt));
	sessionStorage.setItem(COUNTDOWN_END_KEY, String(timing.countdownEndsAt));
	return timing;
}

export function loadRoundTiming(): RoundTiming | null {
	const roundEndsAt = readTimestamp(ROUND_END_KEY);
	const countdownEndsAt = readTimestamp(COUNTDOWN_END_KEY);
	if (roundEndsAt === null || countdownEndsAt === null) return null;
	return { roundEndsAt, countdownEndsAt };
}

export function clearRoundTiming(): void {
	sessionStorage.removeItem(ROUND_END_KEY);
	sessionStorage.removeItem(COUNTDOWN_END_KEY);
}
