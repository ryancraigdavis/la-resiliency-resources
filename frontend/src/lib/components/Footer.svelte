<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { formatDate, t } from '$lib/i18n';
	import { LANGUAGES, htmlLang } from '$lib/languages';
	import { href } from '$lib/paths';

	interface Props {
		lang: string;
		ui: Record<string, string>;
		updated: string;
		machineTranslated: boolean;
	}

	let { lang, ui, updated, machineTranslated }: Props = $props();
</script>

<footer class="site-footer">
	<div class="container stack">
		{#if machineTranslated}
			<p class="note"><Icon name="languages" size={20} /> {ui.machine_translated}</p>
		{/if}
		<p class="note"><Icon name="shield-check" size={20} /> {ui.privacy_note}</p>
		<p>{ui.footer_about} {t(ui, 'checked_on', { date: formatDate(updated, lang) })}</p>
		<nav class="links no-print">
			<a href={href(`/${lang}/print/`)}><Icon name="printer" size={20} /> {ui.print_list}</a>
		</nav>
		<nav class="languages no-print" aria-label={ui.choose_language}>
			{#each LANGUAGES as language (language.code)}
				<a href={href(`/${language.code}/`)} lang={htmlLang(language.code)} hreflang={htmlLang(language.code)}>
					{language.native}
				</a>
			{/each}
		</nav>
	</div>
</footer>

<style>
	.site-footer {
		margin-top: 3rem;
		padding-block: 1.75rem 2.5rem;
		background: var(--surface-2);
		color: var(--muted);
		font-size: 0.98rem;
	}

	.stack {
		display: grid;
		gap: 0.8rem;
	}

	.note {
		display: flex;
		gap: 0.5rem;
		align-items: flex-start;
	}

	.note :global(.icon) {
		flex: none;
		margin-top: 0.2rem;
	}

	.links a {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-weight: 700;
	}

	.languages {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 1rem;
	}
</style>
