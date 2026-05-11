<script lang="ts">
    import { onMount } from 'svelte';

    let username = "Loading";
    let errorMessage = "";

    onMount(async () => {
        const token = localStorage.getItem("access_token");
        if (!token) {
            errorMessage = "You are not logged in.";
            username = "Guest";
            return;
        }

        try {
            const response = await fetch("https://localhost/users/me/", {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                username = data.username;
            } else {
                errorMessage = "Your session expired. Please log in again.";
                localStorage.removeItem("access_token");
                username = "Guest";
            }
        } catch (error) {
            errorMessage = "Could not connect to the backend server.";
            username = "Guest";
        }
    });


	let data = $state(null);

	async function load_data() {
		const res = await fetch('/api/');
		data = await res.json();
	}

	load_data();

	let messages: string[] = $state([]);
	let socket: WebSocket;

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

	connect();
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

<body>
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
		</div>
	</div>
</body>

<style>
	body {
		background-color: lightblue;
	}
	.square {
		height: 425px;
		width: 400px;
		position: center;
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
		position: center;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.center {
		display: flex;
		justify-content: center;
		align-items: center;
	}
</style>
