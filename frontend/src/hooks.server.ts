import type { Handle } from '@sveltejs/kit';
import { basePath } from '$lib/paths';
import { LANGUAGES, htmlLang } from '$lib/languages';

function pageLanguage(pathname: string) {
	const code = pathname.slice(basePath().length).split('/')[1];
	return LANGUAGES.find((language) => language.code === code);
}

export const handle: Handle = async ({ event, resolve }) => {
	const language = pageLanguage(event.url.pathname);
	return resolve(event, {
		transformPageChunk: ({ html }) =>
			html
				.replace('%lang%', htmlLang(language?.code ?? 'en'))
				.replace('%dir%', language?.dir ?? 'ltr')
	});
};
