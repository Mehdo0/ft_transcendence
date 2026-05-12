<script lang="ts">
    import { onMount } from 'svelte';

    let username = $state("Loading...");
    let errorMessage = $state("");

    let data = $state(null);
    let messages: string[] = $state([]);
    let socket: WebSocket;

    async function load_data() {
        try {
            const res = await fetch('/api/');
            data = await res.json();
        } catch (e) {
            console.error("Failed to load generic data", e);
        }
    }

    function connect() {
        socket = new WebSocket('/ws/');

        socket.onopen = () => {
            console.log("WebSocket connected");
            messages = [...messages, "connected to server"];
        };

        socket.onmessage = (event) => {
            console.log("received:", event.data);
            messages = [...messages, `server: ${event.data}`];
        };

        socket.onclose = () => {
            console.log("WebSocket closed");
            messages = [...messages, "disconnected"];
        };
    }

    function sendMessage() {
        if (socket?.readyState === WebSocket.OPEN) {
            socket.send("hello from browser at " + new Date().toISOString());
        }
    }
    onMount(async () => {
        console.log("onMount fired safely!");

        load_data();
        connect();

        try {
            const response = await fetch("/api/users/me/", {
                method: "GET",
                credentials: 'same-origin',
            });

            if (response.ok) {
                const userData = await response.json();
                username = userData.username;
            } else {
                errorMessage = "Your session expired. Please log in again.";
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

<main style="padding: 2rem; font-family: sans-serif;">
    <h2>Dashboard</h2>

    <p>Welcome back, <strong>{username}</strong>!</p>

    {#if errorMessage}
        <p style="color: red; background: #fee; padding: 1rem; border-radius: 4px;">
            {errorMessage}
        </p>
    {/if}
</main>

<div style="padding: 2rem;">
    <p>Api call:</p>
    <p>{JSON.stringify(data)}</p>

    <p>WebSocket test:</p>
    <button onclick={sendMessage}>
        Send message
    </button>

    <ul>
        {#each messages as msg}
            <li>{msg}</li>
        {/each}
    </ul>
</div>

<!-- 4. FIXED HTML: Replaced <body> with a standard wrapper div -->
<div class="menu-container">
    <div class="center">
        <div class="square">
            <div class="center">
                <a href="/game/in-game"><button>Start game</button></a>
            </div>
            <div class="center">
                <a href="/game/lobby"><button>Join lobby</button></a>
            </div>
            <div class="center">
                <a href="/miscellaneous/ranking"><button>Ranking</button></a>
            </div>
            <div class="center">
                <a href="/miscellaneous/friends"><button>Friends</button></a>
            </div>
            <div class="center">
                <a href="/account/login"><button>Login</button></a>
            </div>
            <div class="center">
                <a href="/account/register"><button>Register</button></a>
            </div>
            <div class="center">
                <button onclick={handleLogout}>Logout</button>
            </div>
        </div>
    </div>
</div>

<style>
    /* Moved the body background color to global scope or a wrapper class */
    :global(body) {
        background-color: lightblue;
    }
    .menu-container {
        width: 100%;
    }
    .square {
        height: 500px;
        width: 400px;
        /* 'position: center' is not valid CSS, removed it */
        margin: 5%;
        border-radius: 10%;
        background-color: blueviolet;
    }
    button {
        border-color: aquamarine;
        align-items: center;
        font-size: large;
        height: 50px;
        width: 200px;
        margin: 5%;
        font-family: Verdana, Geneva, Tahoma, sans-serif;
    }
    .center {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
