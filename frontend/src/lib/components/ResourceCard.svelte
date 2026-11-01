<script lang="ts">
	import Badges from '$lib/components/Badges.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ShareButton from '$lib/components/ShareButton.svelte';
	import { REPORT_URL } from '$lib/config';
	import { formatDate, t } from '$lib/i18n';
	import { LANGUAGES, baseLanguage, htmlLang } from '$lib/languages';
	import { href } from '$lib/paths';
	import type { Phone, Resource } from '$lib/types';

	interface Props {
		resource: Resource;
		lang: string;
		ui: Record<string, string>;
		headingLevel?: 'h1' | 'h2' | 'h3';
		linkTitle?: boolean;
		expanded?: boolean;
		compact?: boolean;
	}

	let {
		resource,
		lang,
		ui,
		headingLevel = 'h3',
		linkTitle = true,
		expanded = false,
		compact = false
	}: Props = $props();

	const MAX_VISIBLE_PHONES = 3;

	let open = $state(false);

	function phoneRank(phone: Phone): number {
		const mine = phone.lang === baseLanguage(lang);
		const general = !phone.lang || phone.lang === 'en';
		return mine ? 0 : general ? 1 : 2;
	}

	const path = $derived(href(`/${lang}/r/${resource.id}/`));
	const title = $derived(resource.headline || resource.name);
	const phones = $derived([...resource.phones].sort((a, b) => phoneRank(a) - phoneRank(b)));
	const collapsePhones = $derived(phones.length > MAX_VISIBLE_PHONES);
	const visiblePhones = $derived(collapsePhones ? phones.slice(0, 2) : phones);
	const hiddenPhones = $derived(collapsePhones ? phones.slice(2) : []);
	const hasDetails = $derived(Boolean(resource.who_its_for || resource.how_to_get_it));
	const textLang = $derived(htmlLang(resource.text_lang));
	const textDir = $derived(LANGUAGES.find((language) => language.code === resource.text_lang)?.dir ?? 'ltr');
	const reportHref = $derived(REPORT_URL.replace('{id}', encodeURIComponent(resource.id)));
	const extraId = $derived(`${resource.id}-details`);
</script>

{#snippet titleText()}
	{#if resource.headline}
		<span lang={textLang} dir={textDir}>{resource.headline}</span>
	{:else}
		<bdi lang="en">{resource.name}</bdi>
	{/if}
{/snippet}

{#snippet phoneLink(phone: Phone, primary: boolean)}
	<a class="button phone {primary ? 'button-primary' : 'button-outline'}" href="tel:{phone.tel}">
		<Icon name="phone" />
		<span class="phone-text">
			<span class="ltr number">{phone.number}</span>
			{#if phone.label}<span class="label" lang={textLang} dir={textDir}>{phone.label}</span>{/if}
		</span>
	</a>
{/snippet}

{#snippet websiteLink()}
	{#if resource.url}
		<a class="button button-outline" href={resource.url} target="_blank" rel="noopener noreferrer">
			<Icon name="external-link" />
			{ui.website}
		</a>
	{/if}
{/snippet}

{#snippet tipNote()}
	{#if resource.tip}
		<p class="tip"><strong>{ui.good_to_know}:</strong> <span lang={textLang} dir={textDir}>{resource.tip}</span></p>
	{/if}
{/snippet}

{#snippet detailList()}
	<dl>
		{#if resource.who_its_for}
			<dt>{ui.who_its_for}</dt>
			<dd lang={textLang} dir={textDir}>{resource.who_its_for}</dd>
		{/if}
		{#if resource.how_to_get_it}
			<dt>{ui.how_to_get_it}</dt>
			<dd lang={textLang} dir={textDir}>{resource.how_to_get_it}</dd>
		{/if}
	</dl>
{/snippet}

{#snippet summaryLabel(label: string)}
	<summary><span>{label}</span><Icon name="chevron-down" size={18} /></summary>
{/snippet}

{#snippet cardFooter()}
	<footer>
		<span>{t(ui, 'checked_on', { date: formatDate(resource.last_verified, lang) })}</span>
		{#if REPORT_URL}
			<a href={reportHref} target="_blank" rel="noopener noreferrer">{ui.report_problem}</a>
		{/if}
	</footer>
{/snippet}

<article class="card" class:urgent={resource.urgent} class:compact class:open id={resource.id}>
	<header>
		<svelte:element this={headingLevel} class="title">
			{#if linkTitle}<a href={path}>{@render titleText()}</a>{:else}{@render titleText()}{/if}
		</svelte:element>
		{#if resource.headline}<p class="org"><bdi lang="en">{resource.name}</bdi></p>{/if}
	</header>

	<Badges {resource} {lang} {ui} />

	<p class="description" lang={textLang} dir={textDir}>{resource.description}</p>

	{#if compact}
		<div class="actions">
			{#if phones.length}{@render phoneLink(phones[0], true)}{/if}
			{@render websiteLink()}
			<button
				type="button"
				class="toggle"
				aria-expanded={open}
				aria-controls={extraId}
				onclick={() => (open = !open)}
			>
				<span>{ui.more_details}</span><Icon name="chevron-down" size={18} />
			</button>
		</div>

		<div class="extra" id={extraId} hidden={!open}>
			{@render tipNote()}
			{#if hasDetails}{@render detailList()}{/if}
			<div class="actions">
				{#each phones.slice(1) as phone, i (phone.tel + i)}
					{@render phoneLink(phone, false)}
				{/each}
				<ShareButton {path} {title} {ui} />
			</div>
			{@render cardFooter()}
		</div>
	{:else}
		{@render tipNote()}

		{#if hasDetails}
			<details class="more" open={expanded}>
				{@render summaryLabel(ui.more_details)}
				{@render detailList()}
			</details>
		{/if}

		<div class="actions">
			{#each visiblePhones as phone, i (phone.tel + i)}
				{@render phoneLink(phone, i === 0)}
			{/each}
			{@render websiteLink()}
			<ShareButton {path} {title} {ui} />
		</div>

		{#if hiddenPhones.length}
			<details class="more">
				{@render summaryLabel(ui.more_phone_lines)}
				<div class="actions">
					{#each hiddenPhones as phone, i (phone.tel + i)}
						{@render phoneLink(phone, false)}
					{/each}
				</div>
			</details>
		{/if}

		{@render cardFooter()}
	{/if}
</article>

<style>
	.card {
		display: grid;
		gap: 0.75rem;
		padding: 1.1rem 1.15rem 0.9rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
	}

	.card.urgent {
		border-inline-start: 5px solid var(--urgent);
	}

	.title {
		font-size: 1.25rem;
	}

	:global(h1).title {
		font-size: 1.6rem;
	}

	.title a {
		color: var(--text);
		text-decoration: none;
	}

	.title a:hover {
		text-decoration: underline;
		color: var(--primary);
	}

	.org {
		margin-top: 0.15rem;
		color: var(--muted);
		font-size: 0.98rem;
		font-weight: 700;
	}

	.tip {
		padding: 0.6rem 0.8rem;
		border-inline-start: 4px solid var(--tip-border);
		border-radius: 6px;
		background: var(--surface-2);
	}

	.more summary {
		cursor: pointer;
		color: var(--primary);
		font-weight: 700;
		min-height: 2.75rem;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		list-style: none;
	}

	.more summary::-webkit-details-marker {
		display: none;
	}

	.more summary :global(svg) {
		transition: transform 0.15s ease;
	}

	.more[open] summary :global(svg) {
		transform: rotate(180deg);
	}

	.compact {
		gap: 0.6rem;
		padding-bottom: 1rem;
	}

	.compact.open {
		padding-bottom: 0.5rem;
	}

	.compact .title {
		font-size: 1.15rem;
	}

	.compact .description {
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		overflow: hidden;
	}

	.compact.open .description {
		display: block;
		-webkit-line-clamp: unset;
		line-clamp: unset;
	}

	.toggle {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		min-height: 2.75rem;
		margin-inline-start: auto;
		padding: 0 0.25rem;
		border: 0;
		background: transparent;
		color: var(--primary);
		font: inherit;
		font-weight: 700;
		cursor: pointer;
	}

	.toggle :global(svg) {
		transition: transform 0.15s ease;
	}

	.toggle[aria-expanded='true'] :global(svg) {
		transform: rotate(180deg);
	}

	.extra {
		display: grid;
		gap: 0.75rem;
		padding-bottom: 0.5rem;
	}

	.extra[hidden] {
		display: none;
	}

	dl {
		display: grid;
		gap: 0.2rem;
		margin: 0.25rem 0 0;
	}

	dt {
		font-weight: 700;
	}

	dd {
		margin: 0 0 0.5rem;
	}

	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
	}

	.phone {
		white-space: normal;
		text-align: start;
	}

	.phone-text {
		display: grid;
	}

	.number {
		font-size: 1.1rem;
	}

	.label {
		font-size: 0.85rem;
		font-weight: 600;
		opacity: 0.9;
	}

	footer {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 0.25rem 1rem;
		padding-top: 0.6rem;
		border-top: 1px solid var(--border);
		color: var(--muted);
		font-size: 0.9rem;
	}
</style>
