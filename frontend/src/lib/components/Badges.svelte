<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { t } from '$lib/i18n';
	import { LANGUAGES, baseLanguage } from '$lib/languages';
	import type { Resource } from '$lib/types';

	let { resource, lang, ui }: { resource: Resource; lang: string; ui: Record<string, string> } = $props();

	const AUDIENCE_KEYS: Record<string, string> = {
		church_members: 'church_members',
		seniors: 'seniors',
		families: 'families',
		students: 'students'
	};

	const native = $derived(LANGUAGES.find((language) => language.code === lang)?.native ?? lang);
	const speaksMine = $derived(lang !== 'en' && resource.languages.includes(baseLanguage(lang)));
	const manyLanguages = $derived(resource.multilingual || resource.languages.length > 2);
	const audienceKey = $derived(AUDIENCE_KEYS[resource.audience]);
</script>

<ul class="badges">
	{#if speaksMine}
		<li class="language"><Icon name="languages" size={18} />{t(ui, 'help_in_language', { language: native })}</li>
	{:else if manyLanguages}
		<li class="language"><Icon name="languages" size={18} />{ui.help_in_many_languages}</li>
	{/if}
	{#if resource.status_ok}
		<li class="status"><Icon name="shield-check" size={18} />{ui.status_ok}</li>
	{/if}
	{#if resource.cost === 'free'}
		<li>{ui.free}</li>
	{:else if resource.cost === 'paid'}
		<li>{ui.paid}</li>
	{/if}
	{#if audienceKey}
		<li>{ui[audienceKey]}</li>
	{/if}
</ul>

<style>
	.badges {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.badges:empty {
		display: none;
	}

	li {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.15rem 0.65rem;
		border-radius: 999px;
		background: var(--surface-2);
		color: var(--text);
		font-size: 0.9rem;
		font-weight: 700;
	}

	.language {
		background: var(--lang-soft);
		color: var(--lang-ink);
	}

	.status {
		background: var(--status-soft);
		color: var(--status-ink);
	}
</style>
