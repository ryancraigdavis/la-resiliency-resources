<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import LanguageMenu from '$lib/components/LanguageMenu.svelte';
	import { href } from '$lib/paths';

	let { lang, ui }: { lang: string; ui: Record<string, string> } = $props();

	const crowded = $derived(lang.startsWith('zh-'));
</script>

<header class="site-header">
	<div class="container bar" class:crowded>
		<a class="brand" href={href(`/${lang}/`)} aria-label={ui.site_name}>
			<span class="mark"><Icon name="house" size={20} /></span>
			<span class="name" aria-hidden="true">{ui.site_name}</span>
		</a>
		<LanguageMenu {lang} label={ui.choose_language} />
	</div>
</header>

<style>
	.site-header {
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}

	.bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		min-height: 4rem;
		padding-block: 0.5rem;
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		min-width: 0;
		color: var(--text);
		font-weight: 800;
		font-size: 1rem;
		line-height: 1.25;
		text-decoration: none;
	}

	.name {
		overflow-wrap: normal;
	}

	.mark {
		flex: none;
		display: grid;
		place-items: center;
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 10px;
		background: var(--primary);
		color: var(--primary-ink);
	}

	@media (max-width: 30rem) {
		.crowded .name {
			display: none;
		}
	}
</style>
