import MiniSearch from 'minisearch';
import type { Resource, SearchData } from '$lib/types';
import { baseLanguage } from '$lib/languages';
import { normalize } from './normalize';
import { tokenize } from './tokenize';

const BOOST = {
	name: 3,
	headline: 2.5,
	terms: 2,
	topics: 1.5,
	description: 1,
	details: 0.7,
	english: 0.8
};
const LANGUAGE_BOOST = 1.15;
const NAME_MATCH_BOOST = 3;
const MIN_NAME_MATCH_LENGTH = 3;
const RELATIVE_CUTOFF = 0.2;
const MIN_PREFIX_LENGTH = 3;
const MAX_RESULTS = 30;
const SCRIPT_WITHOUT_SPACES = /[\p{Script=Han}\p{Script=Hangul}]/u;

interface IndexedDoc {
	id: string;
	name: string;
	headline: string;
	terms: string;
	topics: string;
	description: string;
	details: string;
	english: string;
}

export interface SearchIndex {
	search(query: string): Resource[];
}

function englishText(data: SearchData, id: string): string {
	const english = data.english[id];
	return english
		? [english.name, english.headline, english.description, ...english.search_terms, ...english.topics].join(' ')
		: '';
}

function toDoc(resource: Resource, data: SearchData): IndexedDoc {
	return {
		id: resource.id,
		name: resource.name,
		headline: resource.headline,
		terms: resource.search_terms.join(' \n '),
		topics: resource.categories.map((id) => data.topics[id] ?? '').join(' '),
		description: resource.description,
		details: [resource.who_its_for, resource.how_to_get_it, resource.tip].join(' '),
		english: englishText(data, resource.id)
	};
}

function fuzzyFor(term: string): number | false {
	return term.length >= 5 && !SCRIPT_WITHOUT_SPACES.test(term) ? 0.2 : false;
}

function servesLanguage(resource: Resource, lang: string): boolean {
	return resource.multilingual || resource.languages.includes(baseLanguage(lang));
}

function nameMatches(resource: Resource, query: string): boolean {
	const wanted = normalize(query).trim();
	return wanted.length >= MIN_NAME_MATCH_LENGTH && normalize(resource.name).includes(wanted);
}

export function createSearchIndex(data: SearchData, lang: string): SearchIndex {
	const byId = new Map(data.resources.map((resource) => [resource.id, resource]));
	const boosted = new Set(
		data.resources.filter((resource) => lang !== 'en' && servesLanguage(resource, lang)).map((r) => r.id)
	);
	const mini = new MiniSearch<IndexedDoc>({
		fields: Object.keys(BOOST),
		tokenize: (text) => tokenize(text, 'index'),
		processTerm: (term) => term,
		searchOptions: {
			boost: BOOST,
			prefix: (term) => term.length >= MIN_PREFIX_LENGTH,
			fuzzy: fuzzyFor,
			combineWith: 'OR',
			tokenize: (text) => tokenize(text, 'query'),
			boostDocument: (id) => (boosted.has(String(id)) ? LANGUAGE_BOOST : 1)
		}
	});
	mini.addAll(data.resources.map((resource) => toDoc(resource, data)));

	return {
		search(query: string): Resource[] {
			const hits = query.trim() ? mini.search(query) : [];
			const ranked = hits
				.map((hit) => ({ resource: byId.get(String(hit.id)), score: hit.score }))
				.filter((hit): hit is { resource: Resource; score: number } => Boolean(hit.resource))
				.map((hit) => ({
					...hit,
					score: hit.score * (nameMatches(hit.resource, query) ? NAME_MATCH_BOOST : 1)
				}))
				.sort((a, b) => b.score - a.score);
			const cutoff = (ranked[0]?.score ?? 0) * RELATIVE_CUTOFF;
			return ranked
				.filter((hit) => hit.score >= cutoff)
				.slice(0, MAX_RESULTS)
				.map((hit) => hit.resource);
		}
	};
}
