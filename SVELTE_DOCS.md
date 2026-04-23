To run:
```sh
npm install
npm run dev
```

This will automatically detect changes and update so you don't need to rebuild.

.svelte apps combine typescript CSS and HTML

### concepts

Il faut voir Svelte comme un préprocesseur de HTML. Il nous permet de définir du js/ts CSS et HTML dans le même fichier, ce qui est pratique pour garder une vision globale de la page. Mais il étend aussi le HTML pour apporter de la réactivité. Comme avec la rune `$state`

les tags `<script>` sont utilisés pour definir un bout de code, des fonctions ou des imports. `<script lang="ts">` nous permet même d'écrire du typescript inline

then the operators `{}` allow us to define inline code to replace the HTML at runtime

`#props` can be used to pass data or functions to children/imported elements here is an example

```svelte
<script>
	import Stepper from './Stepper.svelte';

	let value = $state(0);
</script>

<p>The current value is {value}</p>

<Stepper 
	increment={() => value += 1} // passing the functions as props here
	decrement={() => value -= 1}
/>
`

```svelte
<script>
	let { increment, decrement } = $props(); // taking the function references here
</script>

<button onclick={decrement}>-1</button> <!-- this sets up an handler to be called when button is pressed -->
<button onclick={increment}>+1</button>

```

this can also be used to pass [event handlers](https://svelte.dev/tutorial/svelte/spreading-events) down to imported elements


### doc:
[svelte doc](https://svelte.dev/tutorial/svelte/)

[events](https://svelte.dev/tutorial/svelte/dom-events)

[Svelte canvas](https://svelte.dev/tutorial/svelte/attach) ← This one is a drawing example that could be very helpful to create our own.

[Svelte vs SvelteKit](https://sveltekit.io/blog/svelte-vs-sveltekit)

[SvelteKit doc](https://svelte.dev/tutorial/kit/)
