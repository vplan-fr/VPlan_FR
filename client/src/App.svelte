<script>
	export let name;
</script>

<main>
	<h1>Hello {name}!</h1>
	<p>Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte apps. <span class="material-symbols-outlined">settings</span></p>
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
</main>

<style lang="scss">
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
		font-size: 4em;
		font-weight: 100;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>