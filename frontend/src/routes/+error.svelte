<script lang="ts">
	import { page } from '$app/state';
	import { LANGUAGES, htmlLang } from '$lib/languages';
	import { href } from '$lib/paths';
</script>

<svelte:head>
	<title>{page.status}</title>
</svelte:head>

<main class="container error">
	<h1>{page.status}</h1>
	<ul>
		{#each LANGUAGES as language (language.code)}
			<li><a href={href(`/${language.code}/`)} lang={htmlLang(language.code)}>{language.native}</a></li>
		{/each}
	</ul>
</main>

<style>
	.error {
		display: grid;
		gap: 1rem;
		padding-block: 3rem;
	}

	ul {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1.25rem;
		padding: 0;
		list-style: none;
		font-size: 1.25rem;
	}
</style>
