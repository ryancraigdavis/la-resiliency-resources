import meta from '$lib/data/meta.json';
import type { LanguageInfo } from '$lib/types';

export const LANGUAGES = meta.languages as LanguageInfo[];
export const LANG_CODES = LANGUAGES.map((language) => language.code);
export const TOPIC_IDS: string[] = meta.topics;

const BCP47: Record<string, string> = { 'zh-hans': 'zh-Hans', 'zh-hant': 'zh-Hant' };
const TRADITIONAL_REGIONS = ['tw', 'hk', 'mo', 'hant'];

export function htmlLang(code: string): string {
	return BCP47[code] ?? code;
}

export function baseLanguage(code: string): string {
	return code.split('-')[0];
}

function chineseVariant(parts: string[]): string {
	return parts.some((part) => TRADITIONAL_REGIONS.includes(part)) ? 'zh-hant' : 'zh-hans';
}

function matchOne(tag: string): string | undefined {
	const parts = tag.toLowerCase().split(/[-_]/);
	const candidate = parts[0] === 'zh' ? chineseVariant(parts) : parts[0];
	return LANG_CODES.find((code) => code === candidate);
}

export function matchLanguage(preferred: readonly string[]): string | undefined {
	return preferred.map(matchOne).find(Boolean);
}

export function swapLanguage(pathname: string, base: string, lang: string): string {
	const rest = pathname.slice(base.length).split('/').slice(2).join('/');
	return `${base}/${lang}/${rest}`;
}
