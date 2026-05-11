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
		// not JSON, fall through
	}
	return res.statusText || 'Erreur inconnue';
}

async function asResult<T>(res: Response): Promise<ApiResult<T>> {
	if (!res.ok) {
		return { ok: false, status: res.status, detail: await readError(res) };
	}
	if (res.status === 204) return { ok: true, data: undefined as T };
	try {
		const data = (await res.json()) as T;
		return { ok: true, data };
	} catch {
		return { ok: true, data: undefined as T };
	}
}

export async function registerUser(
	username: string,
	email: string,
	password: string
): Promise<ApiResult<{ user_created: string }>> {
	const qs = new URLSearchParams({ username, email, password }).toString();
	const res = await fetch(`${API_REGISTER}?${qs}`, {
		...FETCH_BASE,
		method: 'POST'
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
