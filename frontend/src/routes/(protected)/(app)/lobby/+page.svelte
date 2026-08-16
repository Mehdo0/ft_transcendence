<script lang="ts">
	import { goto } from '$app/navigation';
	import { send, subscribe } from '$lib/stores/wsManager';
	import { onMount } from 'svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import PageTitle from '$lib/components/PageTitle.svelte';

	let lobbyCode = $state('');
	let joinError = $state(false);

	const boxClasses = 'flex flex-1 flex-col justify-between border-4 border-ink bg-bg-alt p-6';
	const boxTitleClasses = 'mb-3 text-2xl uppercase';
	const boxTextClasses = 'mb-6 text-sm leading-normal text-muted';

	onMount(() => {
		const unsubscribe = subscribe((message) => {
			if (message.type === 'lobby_created' || message.type === 'lobby_joined') {
				goto('/lobby/' + message.code);
			} else if (message.type === 'error') {
				joinError = true;
				setTimeout(() => (joinError = false), 500);
			}
		});

		return () => {
			unsubscribe();
		};
	});

	function createLobby() {
		send({ type: 'create_lobby' });
	}

	function joinLobby() {
		const code = lobbyCode.trim().toUpperCase();
		if (code.length !== 6 || !code.split('').every((c) => /[A-Z0-9]/.test(c))) return;
		send({ type: 'join_lobby', code });
	}
</script>

<svelte:head>
	<title>Private Match — Draw Meter</title>
</svelte:head>

<div class="flex flex-1 items-center justify-center py-8">
	<div
		class="flex w-full max-w-[760px] flex-col items-center border-4 border-ink bg-bg p-6 shadow-nb-lg"
	>
		<PageTitle title="Private Match" class="text-center" />
		<p class="mt-1 mb-8 text-xl text-muted">Play against your friends</p>

		<div class="flex w-full flex-col items-stretch gap-6 md:flex-row">
			<div class={boxClasses}>
				<h3 class={boxTitleClasses}>Host a Game</h3>
				<p class={boxTextClasses}>
					Generate a secure room and invite your friends via a secret code.
				</p>
				<Button variant="primary" onclick={createLobby} class="h-13 w-full">Create Lobby</Button>
			</div>

			<div
				class="flex items-center justify-center font-display text-sm font-extrabold text-muted md:justify-start"
				aria-hidden="true"
			>
				<span class="border-4 border-ink bg-bg px-2 py-1">OR</span>
			</div>

			<div class={boxClasses}>
				<h3 class={boxTitleClasses}>Join a Game</h3>
				<p class={boxTextClasses}>Enter a secret code provided by the host to join their lobby.</p>

				<div class="flex flex-col gap-3">
					<Input
						mono
						type="text"
						bind:value={lobbyCode}
						oninput={() =>
							(lobbyCode = lobbyCode
								.toUpperCase()
								.replace(/[^A-Z0-9]/g, '')
								.slice(0, 6))}
						placeholder="AB12C3"
						maxlength="6"
						aria-label="Lobby code"
						onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && joinLobby()}
						class="text-center text-2xl {joinError ? 'animate-shake border-danger' : ''}"
					/>
					<Button
						variant="accent"
						onclick={joinLobby}
						disabled={lobbyCode.length !== 6}
						class="h-13 w-full"
					>
						Join
					</Button>
				</div>
			</div>
		</div>
	</div>
</div>
