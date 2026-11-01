<script lang="ts">
	import Footer from '$lib/components/Footer.svelte';
	import Header from '$lib/components/Header.svelte';
	import { SITE_URL } from '$lib/config';
	import { LANGUAGES, htmlLang } from '$lib/languages';
	import { page } from '$app/state';

	let { data, children } = $props();

	const alternates = $derived(
		SITE_URL
			? LANGUAGES.map((language) => ({
					hreflang: htmlLang(language.code),
					url: new URL(page.url.pathname.replace(`/${data.lang}/`, `/${language.code}/`), SITE_URL).href
				}))
			: []
	);

	$effect(() => {
		try {
			localStorage.setItem('lang', data.lang);
		} catch {
			// Storage can be unavailable in private browsing; the language chooser still works.
		}
	});
</script>

<svelte:head>
	<meta property="og:site_name" content={data.ui.site_name} />
	<meta property="og:locale" content={htmlLang(data.lang)} />
	{#each alternates as alternate (alternate.hreflang)}
		<link rel="alternate" hreflang={alternate.hreflang} href={alternate.url} />
	{/each}
</svelte:head>

<a class="skip-link" href="#main">{data.ui.skip_to_content}</a>
<Header lang={data.lang} ui={data.ui} />
<main id="main" class="container">
	{@render children()}
</main>
<Footer lang={data.lang} ui={data.ui} updated={data.updated} machineTranslated={data.machineTranslated} />

<style>
	.skip-link {
		position: absolute;
		inset-inline-start: 1rem;
		top: -4rem;
		z-index: 50;
		padding: 0.6rem 1rem;
		background: var(--primary);
		color: var(--primary-ink);
		border-radius: var(--radius-small);
		font-weight: 700;
	}

	.skip-link:focus {
		top: 1rem;
	}

	main {
		padding-top: 1.25rem;
	}
</style>
