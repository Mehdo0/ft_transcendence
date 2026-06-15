<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    
    let { children } = $props();
    let checking = $state(true);

    onMount(async () => {
        const res = await fetch('/api/users/me/', { credentials: 'same-origin' });
        if (!res.ok) {
            goto('/account/login');
            return;
        }
        checking = false;
    });
</script>

{#if checking}
    <div style="display: flex; justify-content: center; align-items: center; min-height: 50vh;">
        <p style="font-family: var(--font-display); color: var(--c-muted);">Checking authentication...</p>
    </div>
{:else}
    {@render children()}
{/if}
