import { json } from '@sveltejs/kit';
import { LANGUAGES } from '$lib/languages';
import { searchData } from '$lib/server/data';

export const prerender = true;

export function entries() {
	return LANGUAGES.map((language) => ({ lang: language.code }));
}

export function GET({ params }) {
	return json(searchData(params.lang));
}
