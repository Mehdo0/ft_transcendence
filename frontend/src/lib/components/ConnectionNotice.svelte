<script lang="ts">
	import { onMount } from 'svelte';
	import {
		subscribeConnection,
		takeOverConnection,
		type ConnectionStatus
	} from '$lib/stores/wsManager';

	let status = $state<ConnectionStatus>('disconnected');

	onMount(() => subscribeConnection((nextStatus) => (status = nextStatus)));
</script>

{#if status === 'replaced'}
	<div
		class="fixed right-4 bottom-4 z-[2000] flex max-w-[calc(100%-2rem)] items-center gap-4 border-4 border-ink bg-bg px-4 py-3 shadow-nb"
		role="status"
		aria-live="polite"
	>
		<p class="font-mono text-sm font-bold">Session moved to another tab</p>
		<button
			class="shrink-0 cursor-pointer border-b-2 border-ink font-mono text-xs font-bold uppercase"
			onclick={() => void takeOverConnection()}
		>
			Use this tab
		</button>
	</div>
{/if}
