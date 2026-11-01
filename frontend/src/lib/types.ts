export interface Phone {
	number: string;
	tel: string;
	label: string;
	lang: string | null;
}

export interface Resource {
	id: string;
	categories: string[];
	name: string;
	url: string | null;
	headline: string;
	description: string;
	who_its_for: string;
	how_to_get_it: string;
	tip: string;
	phones: Phone[];
	search_terms: string[];
	audience: 'everyone' | 'church_members' | 'seniors' | 'families' | 'students';
	status_ok: boolean;
	cost: '' | 'free' | 'paid' | 'varies';
	languages: string[];
	multilingual: boolean;
	urgent: boolean;
	volatile: boolean;
	last_verified: string;
	text_lang: string;
	machine_translated: boolean;
}

export interface Category {
	id: string;
	icon: string;
	urgent: boolean;
	label: string;
	blurb: string;
	count: number;
}

export interface SiteDoc {
	lang: string;
	dir: 'ltr' | 'rtl';
	updated: string;
	machine_translated: boolean;
	ui: Record<string, string>;
	categories: Category[];
	resources: Resource[];
}

export interface LanguageInfo {
	code: string;
	native: string;
	dir: 'ltr' | 'rtl';
}

export interface EnglishText {
	name: string;
	headline: string;
	description: string;
	search_terms: string[];
	topics: string[];
}

export interface SearchData {
	resources: Resource[];
	topics: Record<string, string>;
	english: Record<string, EnglishText>;
}
