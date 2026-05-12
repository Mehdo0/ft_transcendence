<script lang="ts">
    import { onMount } from 'svelte';

    let username = $state("Loading...");
    let errorMessage = $state("");

    onMount(async () => {
        try {
            const response = await fetch("/api/users/me/", {
                method: "GET",
                credentials: 'same-origin',
            });

            if (response.ok) {
                const userData = await response.json();
                username = userData.username;
            } else {
                errorMessage = "You are not logged in.";
                username = "Guest";
            }
        } catch (error) {
            errorMessage = "Could not connect to the backend server.";
            username = "Guest";
        }
    });

    async function handleLogout() {
   		await fetch("/api/logout", {
     		credentials: 'same-origin',
     		method: 'POST'
     	})
     	window.location.reload();
    }
</script>

<div class="dashboard-wrapper">

    <!-- Welcome Header -->
    <header class="dashboard-header">
        <p>Welcome back, <strong>{username}</strong>!</p>

        {#if errorMessage}
            <div class="error-banner">
                {errorMessage}
            </div>
        {/if}
    </header>

    <!-- Main Navigation Card -->
    <main class="menu-card">
        <a href="/game/in-game" class="menu-btn">Start game</a>
        <a href="/game/lobby" class="menu-btn">Join lobby</a>
        <a href="/ranking" class="menu-btn">Ranking</a>
        
        <!-- Optional: A divider to separate game actions from account actions -->
        <hr class="divider" />
        
        <a href="/account/login" class="menu-btn secondary">Login</a>
        <a href="/account/register" class="menu-btn secondary">Register</a>
    </main>

</div>

<style>
    /* You can remove this global body style if you are already handling it in +layout.svelte */
    :global(body) {
        background-color: lightblue;
        margin: 0;
        font-family: Verdana, Geneva, Tahoma, sans-serif;
    }

    .dashboard-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2rem;
    }

    .dashboard-header {
        text-align: center;
        margin-bottom: 2rem;
        color: #333;
    }

    .dashboard-header h2 {
        margin: 0 0 0.5rem 0;
        font-size: 2rem;
    }

    .error-banner {
        color: red;
        background-color: #fee;
        padding: 1rem;
        border-radius: 6px;
        margin-top: 1rem;
        font-weight: bold;
    }

    /* The Purple Square modernized into a flexbox card */
    .menu-card {
        background-color: blueviolet;
        width: 100%;
        max-width: 400px;
        padding: 2.5rem;
        border-radius: 12px; /* Smoother, modern radius instead of 10% */
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        gap: 1.2rem; /* This creates perfect spacing between buttons automatically */
        box-sizing: border-box;
    }

    .divider {
        border: 0;
        height: 1px;
        background-color: rgba(255, 255, 255, 0.3);
        margin: 0.5rem 0;
    }

    /* Anchor tags styled to look exactly like your old buttons */
    .menu-btn {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: white;
        color: blueviolet;
        text-decoration: none;
        border: 3px solid aquamarine;
        border-radius: 8px;
        height: 50px;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .menu-btn:hover {
        background-color: aquamarine;
        color: #333;
        transform: translateY(-2px); /* Slight lift effect on hover */
    }

    /* A slightly different style for login/register to separate them visually */
    .menu-btn.secondary {
        background-color: transparent;
        color: white;
        border-color: white;
    }

    .menu-btn.secondary:hover {
        background-color: white;
        color: blueviolet;
    }
</style>