<script lang="ts">
    import { page } from '$app/stores';
    import favicon from '$lib/Draw_meter_logo.svg';

    let { children } = $props();

    // Define the main navigation links for the app
    const navLinks = [
        { href: '/', label: 'Dashboard' },
        { href: '/game/lobby', label: 'Play' },
        { href: '/ranking', label: 'Leaderboard' },
    ];
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <title>Draw Meter</title>
</svelte:head>

<div class="app-layout">
    <!-- Top Navigation Bar -->
    <header class="navbar">
        <div class="nav-container">
            
            <!-- Brand / Logo Area -->
            <a href="/" class="nav-brand">
                <img src={favicon} alt="Logo" class="nav-logo" />
                <span class="nav-title">Draw Meter</span>
            </a>

            <!-- Main Navigation Links -->
            <nav class="nav-menu">
                <ul>
                    {#each navLinks as link}
                        <li>
                            <!-- 
                              $page.url.pathname checks the current URL.
                              If it matches the link, it applies the "active" CSS class.
                            -->
                            <a 
                                href={link.href} 
                                class="nav-link"
                                class:active={$page.url.pathname === link.href}
                            >
                                {link.label}
                            </a>
                        </li>
                    {/each}
                </ul>
            </nav>

            <!-- Action Area (Login / Register) -->
            <div class="nav-actions">
                <a href="/account/login" class="btn-login">Login</a>
                <a href="/account/register" class="btn-register">Register</a>
            </div>

        </div>
    </header>

    <!-- Main Content Area where your +page.svelte files will render -->
    <main class="content-wrapper">
        {@render children()}
    </main>
</div>

<style>
    /* 
      Global reset for the entire app. 
      You can move this to an app.css file if you prefer. 
    */
    :global(body) {
        margin: 0;
        padding: 0;
        font-family: 'Source Sans Pro', Verdana, sans-serif;
        background-color: lightblue;
        color: #333;
    }

    /* Structural Layout */
    .app-layout {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    /* Navbar Styling */
    .navbar {
        background-color: white;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
        height: 70px;
    }

    /* Brand / Logo */
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        color: blueviolet;
    }

    .nav-logo {
        height: 35px;
        width: auto;
    }

    .nav-title {
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Navigation Links */
    .nav-menu ul {
        display: flex;
        list-style: none;
        gap: 2rem;
        margin: 0;
        padding: 0;
    }

    .nav-link {
        text-decoration: none;
        color: #555;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.5rem 0;
        transition: color 0.2s ease;
        position: relative;
    }

    .nav-link:hover {
        color: blueviolet;
    }

    /* The glowing underline for the active page */
    .nav-link.active {
        color: blueviolet;
    }

    .nav-link.active::after {
        content: '';
        position: absolute;
        bottom: -4px;
        left: 0;
        width: 100%;
        height: 3px;
        background-color: blueviolet;
        border-radius: 2px;
    }

    /* Buttons */
    .nav-actions {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    .btn-login {
        text-decoration: none;
        color: #555;
        font-weight: 600;
        transition: color 0.2s ease;
    }

    .btn-login:hover {
        color: blueviolet;
    }

    .btn-register {
        text-decoration: none;
        background-color: blueviolet;
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 6px;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }

    .btn-register:hover {
        background-color: #7a1cd1;
    }

    /* Main Content Area */
    .content-wrapper {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        padding: 2rem;
        max-width: 1200px;
        width: 100%;
        margin: 0 auto;
        box-sizing: border-box;
    }
</style>