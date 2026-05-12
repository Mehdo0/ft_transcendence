<script lang="ts">
	import { onMount } from "svelte";

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
    onMount(async () =>{
        load_data();
        connect();
    });
</script>

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
