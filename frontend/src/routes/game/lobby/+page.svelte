<script lang="ts">
    function connect() {
        console.log("Joining lobby...");
        const ws = new WebSocket('wss://localhost/ws/');
        
    }
</script>

<h1>Lobby</h1>
<button onclick={connect}>Join lobby</button>
