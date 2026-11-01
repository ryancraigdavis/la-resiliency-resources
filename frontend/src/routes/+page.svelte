<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { LANG_CODES, htmlLang } from '$lib/languages';
	import { basePath, href } from '$lib/paths';

	let { data } = $props();

	const redirect = `(function () {
		var codes = ${JSON.stringify(LANG_CODES)};
		var base = ${JSON.stringify(basePath())};
		function pick(tag) {
			var parts = String(tag).toLowerCase().split(/[-_]/);
			if (parts[0] !== 'zh') return parts[0];
			return /^(tw|hk|mo|hant)$/.test(parts[1] || '') || parts.indexOf('hant') > -1 ? 'zh-hant' : 'zh-hans';
		}
		var saved = null;
		try { saved = localStorage.getItem('lang'); } catch (e) {}
		var wanted = [saved].concat(navigator.languages || [navigator.language]).filter(Boolean);
		for (var i = 0; i < wanted.length; i++) {
			var code = codes.indexOf(wanted[i]) > -1 ? wanted[i] : pick(wanted[i]);
			if (codes.indexOf(code) > -1) { location.replace(base + '/' + code + '/' + location.search); return; }
		}
	})();`;
</script>

<svelte:head>
	<title>{data.choices[0].siteName}</title>
	<meta name="description" content={data.choices.map((choice) => choice.siteName).join(' · ')} />
	{@html `<script>${redirect}</script>`}
</svelte:head>

<main class="container chooser">
	<div class="mark" aria-hidden="true"><Icon name="languages" size={34} /></div>
	<h1 class="visually-hidden">
		{#each data.choices as choice (choice.code)}
			<span lang={htmlLang(choice.code)} dir={choice.dir}>{choice.choose}.</span>
		{/each}
	</h1>
	<ul>
		{#each data.choices as choice (choice.code)}
			<li>
				<a href={href(`/${choice.code}/`)} lang={htmlLang(choice.code)} dir={choice.dir} hreflang={htmlLang(choice.code)}>
					<span class="native">{choice.native}</span>
					<span class="name">{choice.siteName}</span>
					<span class="choose">{choice.choose}<Icon name="arrow-left" size={18} /></span>
				</a>
			</li>
		{/each}
	</ul>
</main>

<style>
	.chooser {
		display: grid;
		gap: 1.25rem;
		padding-block: 2.5rem;
	}

	.mark {
		display: grid;
		place-items: center;
		width: 4rem;
		height: 4rem;
		border-radius: 18px;
		background: var(--primary);
		color: var(--primary-ink);
	}

	ul {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(min(100%, 14rem), 1fr));
		gap: 0.65rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	a {
		display: grid;
		gap: 0.1rem;
		padding: 1rem 1.1rem;
		background: var(--surface);
		border: 2px solid var(--border);
		border-radius: var(--radius);
		color: var(--text);
		text-decoration: none;
	}

	a:hover {
		border-color: var(--primary);
		color: var(--text);
	}

	.native {
		font-size: 1.5rem;
		font-weight: 800;
	}

	.name {
		font-size: 1rem;
		font-weight: 600;
	}

	.choose {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		margin-top: 0.35rem;
		color: var(--primary);
		font-size: 0.95rem;
		font-weight: 700;
	}

	.choose :global(svg) {
		transform: scaleX(-1);
	}

	[dir='rtl'] .choose :global(svg) {
		transform: none;
	}
</style>
