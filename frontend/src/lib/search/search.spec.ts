import { describe, expect, it } from 'vitest';
import en from '$lib/data/en.json';
import { searchData } from '$lib/server/data';
import type { Resource, SearchData, SiteDoc } from '$lib/types';
import { createSearchIndex } from './engine';
import { normalize } from './normalize';
import { tokenize } from './tokenize';

describe('normalize', () => {
	it.each([
		['İŞ BAŞVURUSU', 'is basvurusu'],
		['kayıt', 'kayit'],
		['Inmigración', 'inmigracion'],
		['كرايه', 'کرایه'],
		['می‌خواهم', 'می خواهم'],
		['۲۱۱ و ٢١١', '211 و 211'],
		['ＣａｌＦｒｅｓｈ', 'calfresh'],
		['집주인', '집주인']
	])('%s → %s', (input, expected) => {
		expect(normalize(input)).toBe(expected);
	});
});

describe('tokenize', () => {
	it.each([
		['免费房租帮助', 'index', ['免费', '费房', '房租', '租帮', '帮助', '免', '费', '房', '租', '帮', '助']],
		['房租', 'query', ['房租']],
		['房', 'query', ['房']],
		['집주인이', 'index', ['집주인이', '집주', '주인', '인이']],
		['음식', 'query', ['음식']],
		['CalFresh 帮助', 'query', ['calfresh', '帮助']]
	] as const)('%s (%s)', (text, mode, expected) => {
		expect(tokenize(text, mode)).toEqual(expected);
	});
});

function englishData(): SearchData {
	const doc = en as SiteDoc;
	const topics = Object.fromEntries(doc.categories.map((c) => [c.id, c.label]));
	return { resources: doc.resources, topics, english: {} };
}

function topIds(data: SearchData, lang: string, query: string, count: number): string[] {
	return createSearchIndex(data, lang)
		.search(query)
		.slice(0, count)
		.map((resource) => resource.id);
}

describe('search over the real English data', () => {
	const data = englishData();

	it.each([
		['eviction', ['tenant-power-toolkit', 'stay-housed-la']],
		['food stamps', ['calfresh']],
		['detained', ['aclu-socal-rapid-response']],
		['calfresh', ['calfresh']],
		['english classes', ['englishconnect']]
	])('"%s" finds %j near the top', (query, expected) => {
		expect(topIds(data, 'en', query, 3)).toEqual(expect.arrayContaining(expected));
	});

	it('tolerates a typo', () => {
		expect(topIds(data, 'en', 'evicton', 3)).toContain('tenant-power-toolkit');
	});

	it('returns nothing for an empty query', () => {
		expect(createSearchIndex(data, 'en').search('   ')).toEqual([]);
	});
});

function resource(id: string, fields: Partial<Resource>): Resource {
	return {
		id,
		categories: ['housing'],
		name: id,
		url: null,
		headline: '',
		description: '',
		who_its_for: '',
		how_to_get_it: '',
		tip: '',
		phones: [],
		search_terms: [],
		audience: 'everyone',
		status_ok: false,
		cost: '',
		languages: [],
		multilingual: false,
		urgent: false,
		volatile: false,
		last_verified: '2026-06-30',
		text_lang: 'en',
		machine_translated: true,
		...fields
	};
}

describe('short words in a sentence do not pull in unrelated resources', () => {
	it.each([
		['en', 'my landlord wants to kick me out', 'mystery-shopping'],
		['es', 'me quieren desalojar', 'medi-cal-full-scope'],
		['es', 'la migra detuvo a mi esposo', 'lausd-free-meals']
	])('[%s] "%s" leaves out %s', (lang, query, unrelated) => {
		const ids = createSearchIndex(searchData(lang), lang)
			.search(query)
			.map((resource) => resource.id);
		expect(ids).not.toContain(unrelated);
	});
});

describe('search in other languages', () => {
	const data: SearchData = {
		topics: { housing: 'Vivienda', food: 'Comida' },
		english: {
			eviction: {
				name: 'Tenant Help',
				headline: 'Legal help if you are being evicted',
				description: 'Eviction defense',
				search_terms: ['eviction', 'landlord'],
				topics: ['Housing']
			}
		},
		resources: [
			resource('eviction', {
				headline: 'Ayuda legal si lo quieren desalojar',
				search_terms: ['desalojo', 'casero', 'کرایه خانه', '집주인이 쫓아내요', '交不起房租', '交不起房租', 'ev sahibi', 'tahliye']
			}),
			resource('food', {
				categories: ['food'],
				search_terms: ['comida gratis', 'غذا', '음식', '免费食物', 'yiyecek', 'iş başvurusu']
			})
		]
	};

	it.each([
		['es', 'desalójo', 'eviction'],
		['es', 'comida', 'food'],
		['fa', 'كرايه', 'eviction'],
		['fa', 'غذا', 'food'],
		['ko', '집주인', 'eviction'],
		['ko', '음식', 'food'],
		['zh-hans', '房租', 'eviction'],
		['zh-hant', '食物', 'food'],
		['tr', 'tahliye', 'eviction'],
		['tr', 'is basvurusu', 'food'],
		['es', 'landlord', 'eviction']
	])('[%s] "%s" finds %s first', (lang, query, expected) => {
		expect(topIds(data, lang, query, 1)).toEqual([expected]);
	});

	it('ranks a resource that serves your language higher on a tie', () => {
		const twins: SearchData = {
			topics: {},
			english: {},
			resources: [
				resource('english-only', { search_terms: ['변호사'] }),
				resource('speaks-korean', { search_terms: ['변호사'], languages: ['ko'] })
			]
		};
		expect(topIds(twins, 'ko', '변호사', 2)).toEqual(['speaks-korean', 'english-only']);
	});
});
