function readPositiveNumber(value: string | undefined, fallback: number): number {
	const parsed = Number(value);
	return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const reconnectBaseDelay = readPositiveNumber(
	import.meta.env.VITE_WS_RECONNECT_BASE_DELAY,
	500
);

export const reconnectMaxDelay = readPositiveNumber(
	import.meta.env.VITE_WS_RECONNECT_MAX_DELAY,
	4000
);
