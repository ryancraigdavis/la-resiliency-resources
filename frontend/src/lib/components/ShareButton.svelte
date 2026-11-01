<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';

	let { path, title, ui }: { path: string; title: string; ui: Record<string, string> } = $props();
	let copied = $state(false);

	async function copy(url: string) {
		await navigator.clipboard.writeText(url);
		copied = true;
		setTimeout(() => (copied = false), 2500);
	}

	async function share() {
		const url = new URL(path, location.origin).href;
		try {
			await (navigator.share ? navigator.share({ title, url }) : copy(url));
		} catch {
			// The person closed the share sheet or the clipboard was unavailable.
		}
	}
</script>

<button type="button" class="button button-quiet" onclick={share}>
	<Icon name={copied ? 'check' : 'share-2'} />
	<span aria-live="polite">{copied ? ui.link_copied : ui.share}</span>
</button>
