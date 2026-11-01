import { EMERGENCY } from '$lib/config';
import { LANGUAGES } from '$lib/languages';
import { findResource, siteDoc } from '$lib/server/data';

export function entries() {
	return LANGUAGES.map((language) => ({ lang: language.code }));
}

export function load({ params }) {
	const doc = siteDoc(params.lang);
	const emergency = EMERGENCY.flatMap(({ id, textKey, sms }) => {
		const resource = findResource(doc, id);
		return resource?.phones.length ? [{ resource, textKey, sms }] : [];
	});
	return { emergency };
}
