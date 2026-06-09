import { redirect } from '@sveltejs/kit';

export async function load({ fetch }) {
	const res = await fetch('/api/users/me/', { credentials: 'same-origin' });
	if (!res.ok) {
		throw redirect(302, '/account/register');
	}
}
