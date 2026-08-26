export type SessionUser = {
	username: string;
	email: string;
	elo: number;
	is_guest: boolean;
};

export type Session =
	| { authenticated: false; user: null }
	| { authenticated: true; user: SessionUser };

function isSessionUser(value: unknown): value is SessionUser {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
	const user = value as Record<string, unknown>;
	return (
		typeof user.username === 'string' &&
		typeof user.email === 'string' &&
		typeof user.elo === 'number' &&
		typeof user.is_guest === 'boolean'
	);
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
	if (!response.ok) throw new Error(`Session request failed with status ${response.status}`);
	const value: unknown = await response.json();
	if (!value || typeof value !== 'object' || Array.isArray(value)) {
		throw new Error('Invalid session response');
	}
	return value as Record<string, unknown>;
}

export async function getSession(): Promise<Session> {
	const response = await fetch('/api/session/', { credentials: 'same-origin' });
	const value = await readJson(response);
	if (value.authenticated === true && isSessionUser(value.user)) {
		return { authenticated: true, user: value.user };
	}
	return { authenticated: false, user: null };
}

export async function createGuestSession(): Promise<Session> {
	const response = await fetch('/api/guest', {
		method: 'POST',
		credentials: 'same-origin'
	});
	const value = await readJson(response);
	if (!isSessionUser(value.user)) throw new Error('Invalid guest session response');
	return { authenticated: true, user: value.user };
}
