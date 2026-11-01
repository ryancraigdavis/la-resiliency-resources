import { describe, expect, it } from 'vitest';
import { t } from './i18n';
import { htmlLang, matchLanguage, swapLanguage } from './languages';

describe('matchLanguage', () => {
	it.each([
		[['es-MX'], 'es'],
		[['zh-TW'], 'zh-hant'],
		[['zh-Hant-HK'], 'zh-hant'],
		[['zh-CN'], 'zh-hans'],
		[['zh'], 'zh-hans'],
		[['fr-FR', 'fa-IR'], 'fa'],
		[['tr'], 'tr'],
		[['pt-BR'], undefined]
	])('%j → %s', (preferred, expected) => {
		expect(matchLanguage(preferred)).toBe(expected);
	});
});

describe('swapLanguage', () => {
	it.each([
		['/es/', '', 'ko', '/ko/'],
		['/es/food/', '', 'fa', '/fa/food/'],
		['/la/zh-hans/r/211-la/', '/la', 'zh-hant', '/la/zh-hant/r/211-la/']
	])('%s → %s', (path, base, lang, expected) => {
		expect(swapLanguage(path, base, lang)).toBe(expected);
	});
});

describe('t', () => {
	it('fills placeholders and leaves unknown ones', () => {
		expect(t({ k: '{count} of {total}' }, 'k', { count: 3 })).toBe('3 of {total}');
	});

	it('falls back to the key', () => {
		expect(t({}, 'missing')).toBe('missing');
	});

	it('maps Chinese codes to BCP 47', () => {
		expect(htmlLang('zh-hant')).toBe('zh-Hant');
	});
});
