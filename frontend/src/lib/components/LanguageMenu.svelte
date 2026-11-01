<script lang="ts">
	import { page } from '$app/state';
	import Icon from '$lib/components/Icon.svelte';
	import { LANGUAGES, htmlLang, swapLanguage } from '$lib/languages';
	import { basePath } from '$lib/paths';

	let { lang, label }: { lang: string; label: string } = $props();
	let open = $state(false);

	const current = $derived(LANGUAGES.find((language) => language.code === lang));
	const isChinese = $derived(lang.startsWith('zh-'));

	function pathFor(code: string): string {
		return swapLanguage(page.url.pathname, basePath(), code);
	}
</script>

<div class="language-controls">
	{#if isChinese}
		<nav class="script-toggle" aria-label="简体 / 繁體">
			<a href={pathFor('zh-hans')} lang="zh-Hans" aria-current={lang === 'zh-hans' ? 'true' : undefined}>简</a>
			<a href={pathFor('zh-hant')} lang="zh-Hant" aria-current={lang === 'zh-hant' ? 'true' : undefined}>繁</a>
		</nav>
	{/if}
	<details class="language-menu" bind:open>
		<summary aria-label={label}>
			<Icon name="languages" />
			<span>{current?.native}</span>
			<Icon name="chevron-down" size={18} />
		</summary>
		<ul>
			{#each LANGUAGES as language (language.code)}
				<li>
					<a
						href={pathFor(language.code)}
						lang={htmlLang(language.code)}
						dir={language.dir}
						hreflang={htmlLang(language.code)}
						aria-current={language.code === lang ? 'true' : undefined}
						onclick={() => (open = false)}
					>
						{language.native}
						{#if language.code === lang}<Icon name="check" size={18} />{/if}
					</a>
				</li>
			{/each}
		</ul>
	</details>
</div>

<style>
	.language-controls {
		flex: none;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.script-toggle {
		display: flex;
		border: 2px solid var(--border);
		border-radius: 999px;
		overflow: hidden;
	}

	.script-toggle a {
		padding: 0.35rem 0.8rem;
		text-decoration: none;
		color: var(--text);
		font-weight: 700;
	}

	.script-toggle a[aria-current='true'] {
		background: var(--primary);
		color: var(--primary-ink);
	}

	.language-menu {
		position: relative;
	}

	summary {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		min-height: 2.75rem;
		padding: 0.35rem 0.7rem;
		border: 2px solid var(--primary);
		border-radius: 999px;
		color: var(--primary);
		font-weight: 700;
		cursor: pointer;
		list-style: none;
		background: var(--surface);
	}

	summary::-webkit-details-marker {
		display: none;
	}

	ul {
		position: absolute;
		inset-inline-end: 0;
		top: calc(100% + 0.4rem);
		z-index: 20;
		min-width: 12rem;
		max-width: calc(100vw - 2rem);
		margin: 0;
		padding: 0.4rem;
		list-style: none;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-small);
		box-shadow: 0 10px 30px rgb(0 0 0 / 0.18);
	}

	li a {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		min-height: 3rem;
		padding: 0.4rem 0.8rem;
		border-radius: 8px;
		color: var(--text);
		text-decoration: none;
		font-size: 1.15rem;
	}

	li a:hover,
	li a[aria-current='true'] {
		background: var(--primary-soft);
	}
</style>
