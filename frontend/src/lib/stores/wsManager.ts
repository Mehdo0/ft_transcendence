import { getWebSocketUrl, reconnectBaseDelay, reconnectMaxDelay } from '$lib/websocket/config';
import { parseServerMessage, type ServerMessage } from '$lib/websocket/serverMessage';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'replaced';

type MessageHandler = (message: ServerMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

let socket: WebSocket | null = null;
let connectionPromise: Promise<void> | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempt = 0;
let reconnectEnabled = false;
let connectionStatus: ConnectionStatus = 'disconnected';

const messageHandlers: MessageHandler[] = [];
const statusHandlers: StatusHandler[] = [];

function setConnectionStatus(status: ConnectionStatus) {
	if (connectionStatus === status) return;
	connectionStatus = status;
	statusHandlers.forEach((handler) => handler(status));
}

function clearReconnectTimer() {
	if (reconnectTimer === null) return;
	clearTimeout(reconnectTimer);
	reconnectTimer = null;
}

function scheduleReconnect() {
	if (!reconnectEnabled || reconnectTimer !== null || connectionStatus === 'replaced') return;

	const delay = Math.min(reconnectBaseDelay * 2 ** reconnectAttempt, reconnectMaxDelay);
	reconnectAttempt += 1;
	reconnectTimer = setTimeout(() => {
		reconnectTimer = null;
		void connect().catch(() => undefined);
	}, delay);
}

function dispatchMessage(message: ServerMessage) {
	messageHandlers.forEach((handler) => handler(message));
}

function openSocket(): Promise<void> {
	const candidate = new WebSocket(getWebSocketUrl());
	socket = candidate;
	setConnectionStatus('connecting');

	return new Promise<void>((resolve, reject) => {
		let settled = false;

		function resolveConnection() {
			if (settled) return;
			settled = true;
			resolve();
		}

		function rejectConnection() {
			if (settled) return;
			settled = true;
			reject(new Error('WebSocket connection failed'));
		}

		candidate.onmessage = (event: MessageEvent) => {
			try {
				const message = parseServerMessage(JSON.parse(event.data));
				if (!message || socket !== candidate) return;

				if (message.type === 'connection_ready') {
					reconnectAttempt = 0;
					setConnectionStatus('connected');
					resolveConnection();
					return;
				}

				if (message.type === 'connection_replaced') {
					reconnectEnabled = false;
					clearReconnectTimer();
					setConnectionStatus('replaced');
					return;
				}

				dispatchMessage(message);
			} catch {
				console.log('invalid msg');
			}
		};

		candidate.onerror = () => rejectConnection();

		candidate.onclose = () => {
			rejectConnection();
			if (socket !== candidate) return;
			socket = null;
			if (connectionStatus === 'replaced') return;
			setConnectionStatus('disconnected');
			scheduleReconnect();
		};
	});
}

export function connect(): Promise<void> {
	if (connectionStatus === 'replaced') {
		return Promise.reject(new Error('Connection active in another tab'));
	}

	if (socket?.readyState === WebSocket.OPEN && connectionStatus === 'connected') {
		return Promise.resolve();
	}

	if (connectionPromise) return connectionPromise;

	reconnectEnabled = true;
	clearReconnectTimer();

	const pendingConnection = openSocket();
	connectionPromise = pendingConnection;
	pendingConnection.then(
		() => {
			if (connectionPromise === pendingConnection) connectionPromise = null;
		},
		() => {
			if (connectionPromise === pendingConnection) connectionPromise = null;
		}
	);
	return pendingConnection;
}

export function takeOverConnection(): Promise<void> {
	const previousSocket = socket;
	socket = null;
	connectionPromise = null;
	reconnectEnabled = true;
	reconnectAttempt = 0;
	clearReconnectTimer();
	setConnectionStatus('disconnected');
	previousSocket?.close();
	return connect();
}

export function disconnect() {
	reconnectEnabled = false;
	clearReconnectTimer();
	const previousSocket = socket;
	socket = null;
	connectionPromise = null;
	setConnectionStatus('disconnected');
	previousSocket?.close();
}

export function send(message: object) {
	if (connectionStatus === 'replaced') return;

	const data = JSON.stringify(message);
	const sendWhenConnected = () => {
		if (socket?.readyState === WebSocket.OPEN && connectionStatus === 'connected') {
			socket.send(data);
		}
	};

	if (socket?.readyState === WebSocket.OPEN && connectionStatus === 'connected') {
		sendWhenConnected();
		return;
	}

	void connect()
		.then(sendWhenConnected)
		.catch(() => undefined);
}

export function subscribe(handler: MessageHandler) {
	messageHandlers.push(handler);

	return () => {
		const index = messageHandlers.indexOf(handler);
		if (index !== -1) messageHandlers.splice(index, 1);
	};
}

export function subscribeConnection(handler: StatusHandler) {
	statusHandlers.push(handler);
	handler(connectionStatus);

	return () => {
		const index = statusHandlers.indexOf(handler);
		if (index !== -1) statusHandlers.splice(index, 1);
	};
}

export function isOpen() {
	return socket?.readyState === WebSocket.OPEN && connectionStatus === 'connected';
}
