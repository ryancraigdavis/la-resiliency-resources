<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import ResourceCard from '$lib/components/ResourceCard.svelte';
	import { href } from '$lib/paths';

	let { data } = $props();

	const title = $derived(data.resource.headline || data.resource.name);
</script>

<svelte:head>
	<title>{title} · {data.ui.site_name}</title>
	<meta name="description" content={data.resource.description} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={data.resource.description} />
</svelte:head>

<div class="resource">
	<nav class="topics" aria-label={data.ui.all_topics}>
		<a href={href(`/${data.lang}/`)}><Icon name="arrow-left" size={20} /> {data.ui.home}</a>
		{#each data.topics as topic (topic.id)}
			<a href={href(`/${data.lang}/${topic.id}/`)}>{topic.label}</a>
		{/each}
	</nav>

	<ResourceCard resource={data.resource} lang={data.lang} ui={data.ui} headingLevel="h1" linkTitle={false} expanded />

	{#if data.lang !== 'en'}
		<p class="hint"><Icon name="info" size={20} /> {data.ui.interpreter_hint}</p>
	{/if}
</div>

<style>
	.resource {
		display: grid;
		gap: 1rem;
	}

	.topics {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem 1rem;
		font-weight: 700;
	}

	.topics a {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}

	:global([dir='rtl']) .topics :global(.icon) {
		transform: scaleX(-1);
	}

	.hint {
		display: flex;
		gap: 0.5rem;
		color: var(--muted);
	}

	.hint :global(.icon) {
		flex: none;
		margin-top: 0.2rem;
	}
</style>
