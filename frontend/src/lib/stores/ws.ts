type WsMessage = { type?: string; [key: string]: unknown };
type MessageHandler = (message: WsMessage) => void;
type StatusHandler = (status: 'connecting' | 'open' | 'closed' | 'error') => void;

let socket: WebSocket | null = null;
let connectPromise: Promise<WebSocket> | null = null;

const messageHandlers = new Map<string, Set<MessageHandler>>();
const statusHandlers = new Set<StatusHandler>();

function emitMessage(message: WsMessage) {
	if (message.type) {
		messageHandlers.get(message.type)?.forEach((handler) => handler(message));
	}
	messageHandlers.get('*')?.forEach((handler) => handler(message));
}

function emitStatus(status: 'connecting' | 'open' | 'closed' | 'error') {
	statusHandlers.forEach((handler) => handler(status));
}

async function connect() {
	if (socket?.readyState === WebSocket.OPEN) return socket;
	if (socket?.readyState === WebSocket.CONNECTING && connectPromise) return connectPromise;

	socket = new WebSocket('/ws/');
	emitStatus('connecting');

	connectPromise = new Promise((resolve, reject) => {
		const currentSocket = socket!;
		let settled = false;

		currentSocket.onopen = () => {
			settled = true;
			connectPromise = null;
			emitStatus('open');
			resolve(currentSocket);
		};

		currentSocket.onmessage = (event) => {
			const message = JSON.parse(event.data);
			emitMessage(message);
		};

		currentSocket.onclose = () => {
			if (socket === currentSocket) socket = null;
			connectPromise = null;
			emitStatus('closed');
			if (!settled) reject(new Error('WebSocket closed'));
		};

		currentSocket.onerror = () => {
			emitStatus('error');
			if (!settled) reject(new Error('WebSocket error'));
		};
	});

	return connectPromise;
}

function disconnect() {
	connectPromise = null;
	socket?.close();
	socket = null;
	emitStatus('closed');
}

function send(message: unknown) {
	return connect()
		.then((currentSocket) => currentSocket.send(JSON.stringify(message)))
		.catch(() => undefined);
}

function on(type: string, handler: MessageHandler) {
	const handlers = messageHandlers.get(type) ?? new Set<MessageHandler>();
	handlers.add(handler);
	messageHandlers.set(type, handlers);

	return () => {
		handlers.delete(handler);
		if (handlers.size === 0) messageHandlers.delete(type);
	};
}

function onStatus(handler: StatusHandler) {
	statusHandlers.add(handler);

	return () => {
		statusHandlers.delete(handler);
	};
}

function isOpen() {
	return socket?.readyState === WebSocket.OPEN;
}

export const wsManager = {
	connect,
	disconnect,
	send,
	on,
	onStatus,
	isOpen
};
