<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { formatDate, t } from '$lib/i18n';

	let { data } = $props();
</script>

<svelte:head>
	<title>{data.ui.print_heading} · {data.ui.site_name}</title>
</svelte:head>

<div class="print-page">
	<header class="sheet-header">
		<div>
			<h1>{data.ui.print_heading}</h1>
			<p>{data.ui.site_name} · {t(data.ui, 'checked_on', { date: formatDate(data.updated, data.lang) })}</p>
			<p class="help"><strong>{data.ui.emergency_211}</strong></p>
		</div>
		{#if data.qr}
			<figure class="qr">
				{@html data.qr}
				<figcaption>{data.ui.print_scan}<br /><span class="ltr">{data.pageUrl}</span></figcaption>
			</figure>
		{/if}
	</header>

	<button type="button" class="button button-primary no-print" onclick={() => window.print()}>
		<Icon name="printer" />
		{data.ui.print_now}
	</button>

	{#each data.sections as section (section.category.id)}
		{#if section.resources.length}
			<section>
				<h2>{section.category.label}</h2>
				<ul>
					{#each section.resources as resource (resource.id)}
						<li>
							<strong>{#if resource.headline}{resource.headline}{:else}<bdi lang="en">{resource.name}</bdi>{/if}</strong>
							{#if resource.headline}<span class="org"><bdi lang="en">{resource.name}</bdi></span>{/if}
							<span class="description">{resource.description}</span>
							{#if resource.tip}<span class="tip">{resource.tip}</span>{/if}
							{#each resource.phones as phone, i (phone.tel + i)}
								<span class="contact"
									><span class="ltr">☎ {phone.number}</span>{#if phone.label}&nbsp;· {phone.label}{/if}</span
								>
							{/each}
							{#if resource.displayUrl}<span class="contact ltr">{resource.displayUrl}</span>{/if}
						</li>
					{/each}
				</ul>
			</section>
		{/if}
	{/each}
</div>

<style>
	.print-page {
		display: grid;
		gap: 1rem;
	}

	.sheet-header {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	h1 {
		font-size: 1.8rem;
	}

	.help {
		margin-top: 0.4rem;
	}

	.qr {
		margin: 0;
		width: 8.5rem;
		text-align: center;
		font-size: 0.8rem;
	}

	.qr :global(svg) {
		width: 100%;
		height: auto;
		background: #fff;
		padding: 0.35rem;
		border-radius: 6px;
	}

	.button {
		width: fit-content;
	}

	h2 {
		font-size: 1.2rem;
		margin-bottom: 0.4rem;
		padding-bottom: 0.2rem;
		border-bottom: 2px solid var(--text);
	}

	ul {
		columns: 2 18rem;
		column-gap: 1.5rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	li {
		display: grid;
		gap: 0.1rem;
		break-inside: avoid;
		margin-bottom: 0.7rem;
		font-size: 0.95rem;
		line-height: 1.35;
	}

	.org,
	.tip {
		color: var(--muted);
	}

	.contact {
		font-weight: 700;
	}

	@media print {
		:global(.site-header),
		:global(.site-footer),
		:global(.skip-link) {
			display: none !important;
		}

		h1 {
			font-size: 18pt;
		}

		h2 {
			font-size: 12pt;
		}

		li {
			font-size: 9pt;
		}

		.org,
		.tip {
			color: #333;
		}
	}
</style>
