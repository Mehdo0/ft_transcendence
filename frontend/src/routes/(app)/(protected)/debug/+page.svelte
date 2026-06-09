<script lang="ts">
	import { onMount } from 'svelte';

	let data = $state(null);
	let messages: string[] = $state([]);
	let socket: WebSocket;

	async function load_data() {
		try {
			const res = await fetch('/api/');
			data = await res.json();
		} catch (e) {
			console.error('Failed to load generic data', e);
		}
	}

	function connect() {
		socket = new WebSocket('/ws/');

		socket.onopen = () => {
			console.log('WebSocket connected');
			messages = [...messages, 'connected to server'];
		};

		socket.onmessage = (event) => {
			console.log('received:', event.data);
			messages = [...messages, `server: ${event.data}`];
		};

		socket.onclose = () => {
			console.log('WebSocket closed');
			messages = [...messages, 'disconnected'];
		};
	}

	function sendMessage() {
		if (socket?.readyState === WebSocket.OPEN) {
			socket.send('hello from browser at ' + new Date().toISOString());
		}
	}
	onMount(async () => {
		load_data();
		connect();
	});
</script>

<svelte:head>
	<title>Debug — Draw Meter</title>
</svelte:head>

<div class="debug">
	<h1>Debug</h1>

	<section class="nb-card">
		<h2>API call</h2>
		<pre class="dump">{JSON.stringify(data, null, 2)}</pre>
	</section>

	<section class="nb-card">
		<h2>WebSocket test</h2>
		<button class="nb-btn nb-btn--primary" onclick={sendMessage}>Send message</button>
		<ul class="log">
			{#each messages as msg, i (i)}
				<li>{msg}</li>
			{/each}
		</ul>
	</section>
</div>

<style>
	.debug {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
		padding: var(--space-6) 0;
	}

	.debug h1 {
		font-size: var(--fs-2xl);
		text-transform: uppercase;
		margin: 0;
	}

	.debug h2 {
		font-size: var(--fs-lg);
		text-transform: uppercase;
		margin: 0 0 var(--space-3);
	}

	.dump,
	.log {
		font-family: var(--font-mono);
		font-size: var(--fs-sm);
		background: var(--c-bg-alt);
		border: var(--border);
		padding: var(--space-3);
		margin: 0;
		overflow-x: auto;
	}

	.log {
		list-style: none;
		margin-top: var(--space-4);
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}
</style>
