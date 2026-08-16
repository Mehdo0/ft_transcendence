<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { connect } from '$lib/stores/wsManager';

	let { children } = $props();
	let checking = $state(true);

	onMount(async () => {
		const response = await fetch('/api/session/', {
			method: 'GET',
			credentials: 'same-origin'
		});
		const session = await response.json();

		if (!session.authenticated) {
			goto('/account/login');
			return;
		}
		connect();
		checking = false;
	});
</script>

{#if checking}
	<div class="flex min-h-[50vh] items-center justify-center">
		<p class="font-display text-muted">Checking authentication...</p>
	</div>
{:else}
	{@render children()}
{/if}
