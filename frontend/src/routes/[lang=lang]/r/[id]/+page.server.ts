import { error } from '@sveltejs/kit';
import { LANGUAGES } from '$lib/languages';
import { findResource, siteDoc } from '$lib/server/data';

export function entries() {
	const ids = siteDoc('en').resources.map((resource) => resource.id);
	return LANGUAGES.flatMap((language) => ids.map((id) => ({ lang: language.code, id })));
}

export function load({ params }) {
	const doc = siteDoc(params.lang);
	const resource = findResource(doc, params.id);
	if (!resource) error(404);
	const categories = doc.categories.filter((category) => resource.categories.includes(category.id));
	return { resource, topics: categories };
}
