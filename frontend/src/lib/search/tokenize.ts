import { normalize } from './normalize';

const WORD = /[\p{L}\p{N}]+/gu;
const HAN = /\p{Script=Han}+/gu;
const HANGUL = /^\p{Script=Hangul}+$/u;

export type TokenMode = 'index' | 'query';

function ngrams(text: string, size: number): string[] {
	const chars = Array.from(text);
	return chars.slice(0, Math.max(chars.length - size + 1, 0)).map((_, i) => chars.slice(i, i + size).join(''));
}

function hanTokens(run: string, mode: TokenMode): string[] {
	const length = Array.from(run).length;
	const unigrams = mode === 'index' || length === 1 ? Array.from(run) : [];
	return [...ngrams(run, 2), ...unigrams];
}

function hangulTokens(word: string): string[] {
	return Array.from(word).length > 2 ? [word, ...ngrams(word, 2)] : [word];
}

function wordTokens(word: string): string[] {
	return HANGUL.test(word) ? hangulTokens(word) : [word];
}

function splitWords(text: string): string[] {
	return text.replace(HAN, ' ').match(WORD) ?? [];
}

export function tokenize(text: string, mode: TokenMode = 'index'): string[] {
	const normalized = normalize(text);
	const han = (normalized.match(HAN) ?? []).flatMap((run) => hanTokens(run, mode));
	const words = splitWords(normalized).flatMap(wordTokens);
	return [...new Set([...words, ...han])];
}
