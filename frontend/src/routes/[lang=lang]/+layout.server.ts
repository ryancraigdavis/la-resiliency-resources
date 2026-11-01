import { siteDoc } from '$lib/server/data';

export function load({ params }) {
	const doc = siteDoc(params.lang);
	return {
		lang: doc.lang,
		dir: doc.dir,
		ui: doc.ui,
		categories: doc.categories,
		updated: doc.updated,
		machineTranslated: doc.machine_translated
	};
}
