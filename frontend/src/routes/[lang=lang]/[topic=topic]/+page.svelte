<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import ResourceCard from '$lib/components/ResourceCard.svelte';
	import { href } from '$lib/paths';

	let { data } = $props();
</script>

<svelte:head>
	<title>{data.category.label} · {data.ui.site_name}</title>
	<meta name="description" content={data.category.blurb} />
	<meta property="og:title" content={data.category.label} />
	<meta property="og:description" content={data.category.blurb} />
</svelte:head>

<div class="topic">
	<a class="back" href={href(`/${data.lang}/`)}><Icon name="arrow-left" size={20} /> {data.ui.all_topics}</a>

	<header class:urgent={data.category.urgent}>
		<span class="icon-circle"><Icon name={data.category.icon} size={30} /></span>
		<div>
			<h1>{data.category.label}</h1>
			<p>{data.category.blurb}</p>
		</div>
	</header>

	{#if data.lang !== 'en'}
		<p class="hint"><Icon name="info" size={20} /> {data.ui.interpreter_hint}</p>
	{/if}

	<div class="list">
		{#each data.resources as resource (resource.id)}
			<ResourceCard {resource} lang={data.lang} ui={data.ui} headingLevel="h2" compact />
		{/each}
	</div>
</div>

<style>
	.topic {
		display: grid;
		gap: 1.1rem;
	}

	.back {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-weight: 700;
		width: fit-content;
	}

	:global([dir='rtl']) .back :global(.icon) {
		transform: scaleX(-1);
	}

	header {
		display: flex;
		gap: 0.9rem;
		align-items: flex-start;
	}

	.icon-circle {
		flex: none;
		display: grid;
		place-items: center;
		width: 3.5rem;
		height: 3.5rem;
		border-radius: 50%;
		background: var(--primary-soft);
		color: var(--primary);
	}

	.urgent .icon-circle {
		background: var(--urgent);
		color: var(--urgent-ink);
	}

	h1 {
		font-size: clamp(1.6rem, 5.5vw, 2.1rem);
	}

	header p {
		color: var(--muted);
		margin-top: 0.2rem;
	}

	.hint {
		display: flex;
		gap: 0.5rem;
		padding: 0.7rem 0.9rem;
		background: var(--primary-soft);
		border-radius: var(--radius-small);
	}

	.hint :global(.icon) {
		flex: none;
		margin-top: 0.2rem;
	}

	.list {
		display: grid;
		gap: 0.85rem;
	}
</style>
