function readPositiveNumber(value: string | undefined, fallback: number): number {
	const parsed = Number(value);
	return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function readString(value: string | undefined, fallback: string): string {
	return value?.trim() || fallback;
}

const webSocketPath = readString(import.meta.env.VITE_WS_PATH, '/ws/');

export function getWebSocketUrl(): string {
	const url = new URL(webSocketPath, window.location.href);
	url.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	return url.toString();
}

export const reconnectBaseDelay = readPositiveNumber(
	import.meta.env.VITE_WS_RECONNECT_BASE_DELAY,
	500
);

export const reconnectMaxDelay = readPositiveNumber(
	import.meta.env.VITE_WS_RECONNECT_MAX_DELAY,
	4000
);
