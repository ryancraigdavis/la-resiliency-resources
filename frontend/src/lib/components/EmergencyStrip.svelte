<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { t } from '$lib/i18n';
	import type { Resource } from '$lib/types';

	interface Item {
		resource: Resource;
		textKey: string;
		sms: boolean;
	}

	let { items, ui }: { items: Item[]; ui: Record<string, string> } = $props();
</script>

<section class="emergency" aria-labelledby="emergency-title">
	<h2 id="emergency-title"><Icon name="siren" /> {ui.emergency_title}</h2>
	{#each items as item (item.resource.id)}
		{@const phone = item.resource.phones[0]}
		<div class="row">
			<p>{t(ui, item.textKey)}</p>
			<div class="actions">
				<a class="button button-urgent" href="tel:{phone.tel}">
					<Icon name="phone" />
					<span class="ltr">{phone.number}</span>
				</a>
				{#if item.sms}
					<a class="button button-soft" href="sms:{phone.tel}">
						<Icon name="message-square" />
						{ui.text_message}
					</a>
				{/if}
			</div>
		</div>
	{/each}
</section>

<style>
	.emergency {
		display: grid;
		gap: 0.9rem;
		padding: 1rem 1.1rem 1.1rem;
		border: 2px solid var(--urgent-border);
		border-radius: var(--radius);
		background: var(--urgent-soft);
	}

	h2 {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--urgent);
		font-size: 1.25rem;
	}

	.row {
		display: grid;
		gap: 0.55rem;
	}

	.row + .row {
		padding-top: 0.9rem;
		border-top: 1px solid var(--urgent-border);
	}

	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.button-soft {
		background: var(--surface);
		border-color: var(--urgent);
		color: var(--urgent);
	}

	.button-soft:hover {
		color: var(--urgent-hover);
		border-color: var(--urgent-hover);
	}
</style>
