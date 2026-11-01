import { LANGUAGES } from '$lib/languages';
import { siteDoc } from '$lib/server/data';

export function load() {
	const choices = LANGUAGES.map((language) => {
		const { ui } = siteDoc(language.code);
		return { ...language, siteName: ui.site_name, choose: ui.choose_language };
	});
	return { choices };
}
