export type ApiOk<T> = { ok: true; data: T };
export type ApiErr = { ok: false; status: number; detail: string };
export type ApiResult<T> = ApiOk<T> | ApiErr;

const API_REGISTER = '/api/register/';
const API_TOKEN = '/api/token';

const FETCH_BASE: RequestInit = {
	credentials: 'same-origin'
};

async function readError(res: Response): Promise<string> {
	try {
		const body = await res.json();
		if (body && typeof body.detail === 'string') return body.detail;
	} catch {
		return res.statusText || 'Erreur inconnue';
	}
	return res.statusText || 'Erreur inconnue';
}

export async function asResult<T>(res: Response): Promise<ApiResult<T>> {
	if (res.ok) {
		const data = (await res.json()) as T;
		return { ok: true, data };
	}

	return {
		ok: false,
		status: res.status,
		detail: await readError(res)
	};
}

export async function registerUser(
	username: string,
	email: string,
	password: string
): Promise<ApiResult<{ user_created: string }>> {
	const res = await fetch(API_REGISTER, {
		...FETCH_BASE,
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ username, email, password })
	});
	return asResult(res);
}

export async function login(username: string, password: string): Promise<ApiResult<void>> {
	const body = new URLSearchParams({ username, password });
	const res = await fetch(API_TOKEN, {
		...FETCH_BASE,
		method: 'POST',
		headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
		body
	});
	return asResult(res);
}
