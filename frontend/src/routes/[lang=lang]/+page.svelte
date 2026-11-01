<script lang="ts">
	import EmergencyStrip from '$lib/components/EmergencyStrip.svelte';
	import Search from '$lib/components/Search.svelte';
	import TopicGrid from '$lib/components/TopicGrid.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>{data.ui.site_name}</title>
	<meta name="description" content={data.ui.tagline} />
	<meta property="og:title" content={data.ui.site_name} />
	<meta property="og:description" content={data.ui.tagline} />
</svelte:head>

<div class="home">
	<section class="intro">
		<h1>{data.ui.site_name}</h1>
		<p>{data.ui.tagline}</p>
	</section>

	<EmergencyStrip items={data.emergency} ui={data.ui} />

	<Search lang={data.lang} ui={data.ui} />

	<section aria-labelledby="topics-title" class="topics">
		<h2 id="topics-title">{data.ui.browse_topics}</h2>
		<TopicGrid categories={data.categories} lang={data.lang} ui={data.ui} />
	</section>
</div>

<style>
	.home {
		display: grid;
		gap: 1.75rem;
	}

	.intro {
		display: grid;
		gap: 0.35rem;
	}

	h1 {
		font-size: clamp(1.7rem, 6vw, 2.3rem);
	}

	.intro p {
		color: var(--muted);
		font-size: 1.15rem;
	}

	.topics {
		display: grid;
		gap: 0.8rem;
	}

	h2 {
		font-size: 1.3rem;
	}
</style>
