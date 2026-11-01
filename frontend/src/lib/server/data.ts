import type { Category, EnglishText, Resource, SearchData, SiteDoc } from '$lib/types';

const docs = import.meta.glob<SiteDoc>('../data/*.json', { eager: true, import: 'default' });

export function siteDoc(lang: string): SiteDoc {
	return docs[`../data/${lang}.json`];
}

export function findResource(doc: SiteDoc, id: string): Resource | undefined {
	return doc.resources.find((resource) => resource.id === id);
}

export function findCategory(doc: SiteDoc, id: string): Category | undefined {
	return doc.categories.find((category) => category.id === id);
}

export function topicResources(doc: SiteDoc, topic: string): Resource[] {
	const inTopic = doc.resources.filter((resource) => resource.categories.includes(topic));
	return [...inTopic.filter((r) => r.urgent), ...inTopic.filter((r) => !r.urgent)];
}

function topicLabels(doc: SiteDoc): Record<string, string> {
	return Object.fromEntries(doc.categories.map((category) => [category.id, category.label]));
}

function englishText(resource: Resource, labels: Record<string, string>): EnglishText {
	return {
		name: resource.name,
		headline: resource.headline,
		description: resource.description,
		search_terms: resource.search_terms,
		topics: resource.categories.map((id) => labels[id] ?? '')
	};
}

export function searchData(lang: string): SearchData {
	const doc = siteDoc(lang);
	const english = siteDoc('en');
	const labels = topicLabels(english);
	const englishEntries = lang === 'en' ? [] : english.resources.map((r) => [r.id, englishText(r, labels)]);
	return {
		resources: doc.resources,
		topics: topicLabels(doc),
		english: Object.fromEntries(englishEntries)
	};
}
