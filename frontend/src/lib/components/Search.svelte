<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import Icon from '$lib/components/Icon.svelte';
	import ResourceCard from '$lib/components/ResourceCard.svelte';
	import { t } from '$lib/i18n';
	import { href } from '$lib/paths';
	import type { SearchIndex } from '$lib/search/engine';
	import type { SearchData } from '$lib/types';

	let { lang, ui }: { lang: string; ui: Record<string, string> } = $props();

	const URL_DELAY_MS = 400;
	const FIRST_RESULTS = 5;

	let query = $state('');
	let index = $state<SearchIndex | null>(null);
	let loading: Promise<void> | null = null;
	let urlTimer: ReturnType<typeof setTimeout> | undefined;
	let expandedQuery = $state('');

	const trimmed = $derived(query.trim());
	const results = $derived(index && trimmed ? index.search(trimmed) : []);
	const waiting = $derived(Boolean(trimmed) && !index);
	const showAll = $derived(expandedQuery === trimmed);
	const visible = $derived(showAll ? results : results.slice(0, FIRST_RESULTS));
	const hiddenCount = $derived(results.length - visible.length);

	async function buildIndex() {
		const [{ createSearchIndex }, response] = await Promise.all([
			import('$lib/search/engine'),
			fetch(href(`/${lang}/search.json`))
		]);
		const data: SearchData = await response.json();
		index = createSearchIndex(data, lang);
	}

	function ensureIndex() {
		loading ??= buildIndex();
	}

	function syncUrl(value: string) {
		clearTimeout(urlTimer);
		urlTimer = setTimeout(() => {
			const url = new URL(page.url);
			url.search = value ? `?q=${encodeURIComponent(value)}` : '';
			replaceState(url, page.state);
		}, URL_DELAY_MS);
	}

	function onInput() {
		ensureIndex();
		syncUrl(trimmed);
	}

	async function showMore() {
		const firstHidden = results[FIRST_RESULTS];
		expandedQuery = trimmed;
		await tick();
		document.querySelector<HTMLElement>(`#${CSS.escape(firstHidden.id)} .title a`)?.focus();
	}

	function clear() {
		query = '';
		syncUrl('');
	}

	onMount(() => {
		query = new URLSearchParams(location.search).get('q') ?? '';
		if (query) ensureIndex();
		return () => clearTimeout(urlTimer);
	});
</script>

<search class="search">
	<form role="search" onsubmit={(event) => event.preventDefault()}>
		<label for="search-input">{ui.search_label}</label>
		<div class="field">
			<Icon name="search" />
			<input
				id="search-input"
				type="search"
				bind:value={query}
				oninput={onInput}
				onfocus={ensureIndex}
				placeholder={ui.search_placeholder}
				autocomplete="off"
				enterkeyhint="search"
				spellcheck="false"
			/>
			{#if query}
				<button type="button" class="clear" onclick={clear} aria-label={ui.clear_search}>
					<Icon name="x" />
				</button>
			{/if}
		</div>
	</form>

	{#if trimmed}
		<div class="results" aria-live="polite">
			{#if waiting}
				<p class="status">{ui.searching}</p>
			{:else if results.length}
				<h2 class="status">{t(ui, 'results_for', { query: trimmed })} ({results.length})</h2>
				{#if lang !== 'en'}
					<p class="hint"><Icon name="info" size={20} /> {ui.interpreter_hint}</p>
				{/if}
				{#each visible as resource (resource.id)}
					<ResourceCard {resource} {lang} {ui} compact />
				{/each}
				{#if hiddenCount}
					<button type="button" class="button button-outline show-more" onclick={showMore}>
						<Icon name="chevron-down" />
						{t(ui, 'show_more', { count: hiddenCount })}
					</button>
				{/if}
			{:else}
				<p class="status empty">{ui.no_results}</p>
			{/if}
		</div>
	{/if}
</search>

<style>
	.search {
		display: grid;
		gap: 1rem;
	}

	label {
		display: block;
		margin-bottom: 0.45rem;
		font-size: 1.3rem;
		font-weight: 800;
	}

	.field {
		position: relative;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding-inline: 0.9rem 0.4rem;
		background: var(--surface);
		border: 2px solid var(--primary);
		border-radius: var(--radius);
		color: var(--primary);
	}

	.field:focus-within {
		outline: 3px solid var(--focus);
		outline-offset: 2px;
	}

	input {
		flex: 1;
		min-width: 0;
		min-height: 3.5rem;
		border: 0;
		background: transparent;
		color: var(--text);
		font-size: 1.2rem;
		outline: none;
	}

	input::-webkit-search-cancel-button {
		display: none;
	}

	input::placeholder {
		color: var(--muted);
	}

	.clear {
		display: grid;
		place-items: center;
		width: 2.75rem;
		height: 2.75rem;
		border: 0;
		border-radius: 50%;
		background: transparent;
		color: var(--muted);
		cursor: pointer;
	}

	.clear:hover {
		background: var(--surface-2);
	}

	.results {
		display: grid;
		gap: 0.85rem;
	}

	.status {
		font-size: 1.1rem;
		font-weight: 700;
	}

	.empty {
		font-weight: 400;
		padding: 1rem;
		background: var(--surface);
		border: 1px dashed var(--border);
		border-radius: var(--radius);
	}

	.show-more {
		width: 100%;
	}

	.hint {
		display: flex;
		gap: 0.5rem;
		color: var(--muted);
	}
</style>
