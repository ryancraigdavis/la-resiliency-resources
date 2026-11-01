import { error } from '@sveltejs/kit';
import { LANGUAGES, TOPIC_IDS } from '$lib/languages';
import { findCategory, siteDoc, topicResources } from '$lib/server/data';

export function entries() {
	return LANGUAGES.flatMap((language) => TOPIC_IDS.map((topic) => ({ lang: language.code, topic })));
}

export function load({ params }) {
	const doc = siteDoc(params.lang);
	const category = findCategory(doc, params.topic);
	if (!category) error(404);
	return { category, resources: topicResources(doc, params.topic) };
}
