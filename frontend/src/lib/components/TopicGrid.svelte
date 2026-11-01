<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { t } from '$lib/i18n';
	import { href } from '$lib/paths';
	import type { Category } from '$lib/types';

	let { categories, lang, ui }: { categories: Category[]; lang: string; ui: Record<string, string> } =
		$props();
</script>

<ul class="grid">
	{#each categories as category (category.id)}
		<li class:urgent={category.urgent}>
			<a href={href(`/${lang}/${category.id}/`)}>
				<span class="icon-circle"><Icon name={category.icon} size={26} /></span>
				<span class="text">
					<span class="label">{category.label}</span>
					<span class="count">{t(ui, 'resource_count', { count: category.count })}</span>
				</span>
			</a>
		</li>
	{/each}
</ul>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));
		gap: 0.65rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.urgent {
		grid-column: 1 / -1;
	}

	a {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		height: 100%;
		min-height: 4.5rem;
		padding: 0.75rem 0.9rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		color: var(--text);
		text-decoration: none;
	}

	a:hover {
		border-color: var(--primary);
		color: var(--text);
	}

	.icon-circle {
		flex: none;
		display: grid;
		place-items: center;
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		background: var(--primary-soft);
		color: var(--primary);
	}

	.urgent a {
		background: var(--urgent-soft);
		border-color: var(--urgent-border);
	}

	.urgent .icon-circle {
		background: var(--urgent);
		color: var(--urgent-ink);
	}

	.text {
		display: grid;
	}

	.label {
		font-weight: 700;
		line-height: 1.3;
	}

	.count {
		color: var(--muted);
		font-size: 0.9rem;
	}
</style>
