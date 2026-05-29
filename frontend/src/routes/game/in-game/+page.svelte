<script lang="ts">
    import { getWs, setWs } from "$lib/stores/ws";
    import { game } from "$lib/stores/game.svelte";
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    
    type Point = { x: number; y: number };
    type Trait = { color: string; width: number; points: Point[] };

    let canvas: HTMLCanvasElement = $state()!;
    let ratio = $state(1);
    let context: CanvasRenderingContext2D = $state()!;
    let last = $state<Point | null>(null);
    let selectedColor = $state('#000000');
    let lastSelectedColor = $state('#000000');
    let stack = $state<Trait[]>([]);
    let redoStack = $state<Trait[]>([]);

    let lineWidth = $state(1);
    let result = $state<'winner' | 'looser' | null>(null);
    let elo_diff = $state(0);

    const COLORS = [
        '#ff0000', '#00ff00', '#0000ff', '#ffff00', 
        '#00ffff', '#ff00ff', '#000000', '#808080', '#ff8000'
    ];
    function clearSessionData() {
        sessionStorage.removeItem('draw_stack');
        sessionStorage.removeItem('draw_my_score');
        sessionStorage.removeItem('draw_opp_score');
        sessionStorage.removeItem('draw_word');
        sessionStorage.removeItem('draw_opponent');
    }

    onMount(() => {
        const savedStack = sessionStorage.getItem('draw_stack');
        if (savedStack) stack = JSON.parse(savedStack);
        
        const savedMyScore = sessionStorage.getItem('draw_my_score');
        if (savedMyScore) game.my_score = parseFloat(savedMyScore);
        
        const savedOppScore = sessionStorage.getItem('draw_opp_score');
        if (savedOppScore) game.opponent_score = parseFloat(savedOppScore);

        const savedWord = sessionStorage.getItem('draw_word');
        if (savedWord) game.word = savedWord;
        
        const savedOpponent = sessionStorage.getItem('draw_opponent');
        if (savedOpponent) game.opponent = savedOpponent;


        let ws = getWs();
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            ws = new WebSocket('/ws/');
            setWs(ws);
        }

        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          switch (msg.type) {
            case 'ai_guess':
              game.my_score = msg.guess[game.word];
              sessionStorage.setItem('draw_my_score', game.my_score.toString());
              break;
            case 'reconnect_game':
                game.id = msg.game_id;
                game.opponent = msg.opponent;
                game.word = msg.word;
                sessionStorage.setItem('draw_word', game.word);
                sessionStorage.setItem('draw_opponent', game.opponent);
                break;
            case 'opponent_guess':
              game.opponent_score = msg.guess[game.word];
              sessionStorage.setItem('draw_opp_score', game.opponent_score.toString());
              break;
            case 'end_game':
                elo_diff = msg.elo_diff;
                result = msg.status;
                clearSessionData(); // Wipe the memory for the next game
                break;
          }
        };
    });

    $effect(() => {
        sessionStorage.setItem('draw_stack', JSON.stringify(stack));
    });

    $effect(() => {
        if (canvas) {
            context = canvas.getContext('2d')!;
            resize(); 
        }
    });

    function surrender() {
        if (confirm("Are you sure you want to forfeit the match?")) {
            clearSessionData(); // Wipe memory if they quit on purpose
            goto('/');
        }
    }

    function resize() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = canvas.clientWidth * dpr;
        canvas.height = canvas.clientHeight * dpr;
        ratio = canvas.width;
        context.scale(dpr, dpr);
        redraw();
    }

    function redraw() {
        context.clearRect(0, 0, canvas.width, canvas.height);

        for (const trait of stack) {
            if (trait.points.length === 0) continue;

            context.strokeStyle = trait.color;
            context.lineWidth = trait.width * canvas.clientWidth;
            context.lineCap = 'round';
            context.lineJoin = 'round';
            context.beginPath();
            context.moveTo(trait.points[0].x * ratio, trait.points[0].y * ratio);
            for (let i = 1; i < trait.points.length; i++) {
                context.lineTo(trait.points[i].x * ratio, trait.points[i].y * ratio);
            }
            context.stroke();
        }
    }

    function undo() {
        const trait = stack.pop();
        if (!trait) return;
        redoStack.push(trait);
        redraw();
    }

    function redo() {
        const trait = redoStack.pop();
        if (!trait) return;
        stack.push(trait);
        redraw();
    }

    function eraser() {
        selectedColor = '#ffffff';
    }

    function pencil() {
        selectedColor = lastSelectedColor;
    }

    function makeAiGuess() {
        const ws = getWs();
        const image = canvas.toDataURL();
        ws?.send(JSON.stringify({ type: "image", image }));
    }
</script>
<svelte:window onresize={resize} />

<header class="game-header">
    <div class="header-info">
        <h1>Draw!</h1>
        <div class="badges">
            <span class="badge">Word: <strong>{game.word}</strong></span>
            <span class="badge">VS: <strong>{game.opponent}</strong></span>
        </div>
    </div>
    <button class="surrender-btn" onclick={surrender}>
        Surrender ⚑
    </button>
</header>

{#if result}
  <div class="overlay">
    <div class="modal">
        {#if result === 'winner'}
          <h2 class="win-text">🎉 You Won!</h2>
          <p class="elo-text positive">+{elo_diff} Elo</p>
        {:else}
          <h2 class="lose-text">💀 You Lost</h2>
          <p class="elo-text negative">-{elo_diff} Elo</p>
        {/if}
        <button class="primary-btn" onclick={() => goto('/')}>Back to Home</button>
    </div>
  </div>
{/if}

<div class="game">
    <div class="tools">
        {#each COLORS as c}
            <button
                class="swatch"
                style="background:{c}"
                title={c}
                onclick={() => {
                    selectedColor = c;
                    lastSelectedColor = c;
                }}
                aria-label={c}
            ></button>
        {/each}
        <button class:active={selectedColor !== '#ffffff'} onclick={pencil}>✏️</button>
        <input
            type="color"
            bind:value={selectedColor}
            oninput={() => (lastSelectedColor = selectedColor)}
        />
        <button class:active={selectedColor === '#ffffff'} onclick={eraser}>🧹</button>
        <input class="width" type="range" min="1" max="20" step="0.5" bind:value={lineWidth} />
        <button onclick={undo} disabled={stack.length === 0}>↶</button>
        <button onclick={redo} disabled={redoStack.length === 0}>↷</button>
    </div>

    <canvas
        bind:this={canvas}
        onpointerdown={(e) => {
            stack.push({
                color: selectedColor,
                width: lineWidth / 100,
                points: [{ x: e.offsetX / ratio, y: e.offsetY / ratio }]
            });

            redoStack = [];
            last = { x: e.offsetX / ratio, y: e.offsetY / ratio };
        }}
        onpointerup={() => {
            last = null;
            makeAiGuess();
        }}
        onpointerleave={() => (last = null)}
        onpointermove={(e) => {
            if (e.buttons !== 1 || !last) return;

            context.strokeStyle = selectedColor;
            context.lineWidth = stack[stack.length - 1].width * canvas.clientWidth;
            context.lineCap = 'round';
            context.lineJoin = 'round';
            context.beginPath();
            context.moveTo(last.x * ratio, last.y * ratio);
            context.lineTo(e.offsetX * ratio, e.offsetY * ratio);
            context.stroke();

            stack[stack.length - 1].points.push({ x: e.offsetX / ratio, y: e.offsetY / ratio });
            last = { x: e.offsetX / ratio, y: e.offsetY / ratio };
        }}
    ></canvas>

    <div class="bars">
        <div class="loaderBar">
            <div class="loaderBar-fill" style="height: {game.my_score}%"></div>
        </div>
        <div class="loaderBar loaderBar--opponent">
            <div class="loaderBar-fill" style="height: {game.opponent_score}%"></div>
        </div>
    </div>
</div>

<style>
    :global(body) {
        margin: 0;
        font-family: system-ui, sans-serif;
        background: #f4f5f7;
        color: #1f2937;
    }

    /* --- NEW HEADER STYLES --- */
    .game-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: #ffffff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .header-info {
        display: flex;
        align-items: center;
        gap: 2rem;
    }

    .game-header h1 {
        margin: 0;
        color: blueviolet;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .badges {
        display: flex;
        gap: 1rem;
    }

    .badge {
        background: #f3f4f6;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.95rem;
        color: #374151;
    }

    .surrender-btn {
        background: transparent;
        border: 2px solid #ef4444;
        color: #ef4444;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .surrender-btn:hover {
        background: #ef4444;
        color: white;
    }

    /* --- NEW MODAL OVERLAY STYLES --- */
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(4px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal {
        background: white;
        padding: 3rem 4rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    @keyframes popIn {
        0% { transform: scale(0.8); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }

    .win-text {
        color: #10b981;
        font-size: 2.5rem;
        margin: 0;
    }

    .lose-text {
        color: #ef4444;
        font-size: 2.5rem;
        margin: 0;
    }

    .elo-text {
        font-size: 1.3rem;
        font-weight: bold;
        margin: 1rem 0 2.5rem;
        color: #6b7280;
    }

    .elo-text.positive { color: #10b981; }
    .elo-text.negative { color: #ef4444; }

    .primary-btn {
        background: blueviolet;
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: background 0.2s;
    }

    .primary-btn:hover {
        background: #7a1cd1;
    }

    /* --- EXISTING GAME STYLES --- */
    .game {
        --canvas-side: 50vmin;
        --tool-size: calc(var(--canvas-side) * 0.1);
        --tool-gap: 0.5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1.5rem;
        padding: 1rem;
    }

    canvas {
        width: var(--canvas-side);
        height: var(--canvas-side);
        background: #ffffff;
        border: 2px solid #d1d5db;
        border-radius: 12px;
        cursor: crosshair;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .tools {
        display: grid;
        grid-template-columns: repeat(3, var(--tool-size));
        gap: var(--tool-gap);
    }

    .tools > * {
        width: var(--tool-size);
        height: var(--tool-size);
        margin: 0;
        padding: 0;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        background: #ffffff;
        cursor: pointer;
        font-size: calc(var(--tool-size) * 0.5);
        line-height: 1;
        box-sizing: border-box;
        transition: transform 0.1s;
    }

    .tools > *:hover:not(:disabled) {
        transform: scale(1.05);
    }

    .tools > .active {
        border: 2px solid #1f2937;
        background: #f3f4f6;
    }

    .tools > *:disabled {
        opacity: 0.3;
        cursor: not-allowed;
    }

    .tools > .width {
        grid-column: 1 / -1;
        width: 100%;
    }

    .bars {
        display: flex;
        gap: var(--tool-gap);
    }

    .loaderBar {
        width: var(--tool-size);
        height: var(--canvas-side);
        background: #f9f9f9;
        border-radius: 10px;
        border: 2px solid #006dfe;
        position: relative;
        overflow: hidden;
    }

    .loaderBar-fill {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        border-radius: 5px;
        background: repeating-linear-gradient(45deg, #0031f2 0 30px, #006dfe 0 40px);
        background-size: 200% 200%;
        background-position: center bottom;
        transition: height 0.3s ease;
    }

    .loaderBar--opponent {
        background: #fef2f2;
        border-color: #dc2626;
    }

    .loaderBar--opponent .loaderBar-fill {
        background: repeating-linear-gradient(45deg, #991b1b 0 30px, #dc2626 0 40px);
        background-size: 200% 200%;
        background-position: center bottom;
    }
</style>