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
	
export async function asResult<T>(res: Response) {
    if (res.ok) {
        const data = await res.json();
        return { ok: true, data: data as T };
    } else {
        // Parse the error JSON from FastAPI
        const errorData = await res.json().catch(() => ({}));
        
        return { 
            ok: false, 
            // Extract the specific 'detail' string we wrote in Python
            detail: errorData.detail || "An unexpected error occurred." 
        };
    }
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

export async function hashPassword(password: string) {
	// 1. Convert the string password into a byte array
	const encoder = new TextEncoder();
	const data = encoder.encode(password);

	// 2. Ask the browser's built-in Crypto API to hash the bytes using SHA-256
	const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);

	// 3. Convert the resulting ArrayBuffer back into a readable Hexadecimal string
	const hashArray = Array.from(new Uint8Array(hashBuffer));
	const hashHex = hashArray.map((byte) => byte.toString(16).padStart(2, '0')).join('');

	return hashHex;
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
