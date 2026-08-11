let socket: WebSocket | null = null;
const subscribers: ((message: any) => void)[] = [];

export function connect() {
	if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING)
		return;
	socket = new WebSocket('/ws/');

	socket.onmessage = (event) => {
		const message = JSON.parse(event.data);
		subscribers.forEach((handler) => handler(message));
		
	};

	socket.onclose = () => {
		socket = null;
	};
}

export function disconnect() {
	socket?.close();
	socket = null;
}

export function send(message: object) {
	connect();
	if (!socket) return;

	const data = JSON.stringify(message);

	if (socket.readyState === WebSocket.OPEN) {
		socket.send(data);
		return;
	}

	socket.addEventListener('open', () => socket?.send(data), { once: true });
}

export function subscribe(handler: (message: any) => void) {
	subscribers.push(handler);

	return () => {
		const index = subscribers.indexOf(handler);
		if (index !== -1) subscribers.splice(index, 1);
	};
}

export function isOpen() {
	return socket?.readyState === WebSocket.OPEN;
}
