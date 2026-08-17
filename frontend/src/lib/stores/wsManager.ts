let socket: WebSocket | null = null;
let connectionPromise: Promise<void> | null = null;
const subscribers: ((message: any) => void)[] = [];

export function connect(): Promise<void> {
	if (socket?.readyState === WebSocket.OPEN) {
		return Promise.resolve();
	}

	if (connectionPromise) {
		return connectionPromise;
	}

	connectionPromise = new Promise<void>((resolve, reject) => {
		socket = new WebSocket('/ws/');

		socket.onopen = () => {
			connectionPromise = null;
			resolve();
		};

		socket.onmessage = (event: MessageEvent) => {
			try {
				const message = JSON.parse(event.data);
				if (message.type === 'error') {
					alert(message.message);
					return;
				}
				subscribers.forEach((handler) => handler(message));
			} catch {
				console.log("invalid msg");
			}
		};


		socket.onerror = (error: Event) => {
			connectionPromise = null;
			reject(error);
		};

		socket.onclose = () => {
			socket = null;
			connectionPromise = null;
		};
	});

	return connectionPromise;
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
