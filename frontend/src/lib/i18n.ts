import { htmlLang } from '$lib/languages';

export function t(ui: Record<string, string>, key: string, vars: Record<string, string | number> = {}) {
	const template = ui[key] ?? key;
	return template.replace(/\{(\w+)\}/g, (match, name) => String(vars[name] ?? match));
}

export function formatDate(iso: string, lang: string): string {
	const date = new Date(`${iso}T12:00:00`);
	return new Intl.DateTimeFormat(htmlLang(lang), { dateStyle: 'medium' }).format(date);
}

export function languageName(code: string, displayLang: string): string {
	const names = new Intl.DisplayNames([htmlLang(displayLang), 'en'], { type: 'language' });
	return names.of(code) ?? code;
}
