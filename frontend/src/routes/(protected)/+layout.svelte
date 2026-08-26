<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { createGuestSession, getSession } from '$lib/session';
	import { connect } from '$lib/stores/wsManager';

	let { children } = $props();
	let checking = $state(true);
	let navigationVersion = 0;

	function isLobbyPath(pathname: string): boolean {
		return pathname === '/lobby' || pathname.startsWith('/lobby/');
	}

	function allowsGuest(pathname: string): boolean {
		return isLobbyPath(pathname) || pathname === '/ranking' || pathname === '/in-game';
	}

	function needsWebSocket(pathname: string): boolean {
		return isLobbyPath(pathname) || pathname === '/in-game' || pathname === '/start_game';
	}

	async function initialize(pathname: string, version: number): Promise<void> {
		try {
			let session = await getSession();
			if (!session.authenticated && allowsGuest(pathname)) {
				session = await createGuestSession();
			}

			if (!session.authenticated || (session.user.is_guest && !allowsGuest(pathname))) {
				await goto(resolve('/account/login'));
				return;
			}
			if (needsWebSocket(pathname)) await connect();
			if (version === navigationVersion) checking = false;
		} catch {
			await goto(resolve('/'));
		}
	}

	$effect(() => {
		const pathname = page.url.pathname;
		const version = ++navigationVersion;
		checking = true;
		void initialize(pathname, version);
	});
</script>

{#if checking}
	<div class="flex min-h-[50vh] items-center justify-center">
		<p class="font-display text-muted">Checking authentication...</p>
	</div>
{:else}
	{@render children()}
{/if}
