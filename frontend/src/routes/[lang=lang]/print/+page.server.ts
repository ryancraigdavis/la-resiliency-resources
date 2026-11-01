import QRCode from 'qrcode';
import { SITE_URL } from '$lib/config';
import { href } from '$lib/paths';
import { siteDoc } from '$lib/server/data';

function displayUrl(url: string): string {
	return url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
}

export async function load({ params }) {
	const doc = siteDoc(params.lang);
	const sections = doc.categories.map((category) => ({
		category,
		resources: doc.resources
			.filter((resource) => resource.categories[0] === category.id)
			.map((resource) => ({ ...resource, displayUrl: resource.url ? displayUrl(resource.url) : '' }))
	}));
	const pageUrl = SITE_URL ? new URL(href(`/${params.lang}/`), SITE_URL).href : '';
	const qr = pageUrl ? await QRCode.toString(pageUrl, { type: 'svg', margin: 0, errorCorrectionLevel: 'M' }) : '';
	return { sections, qr, pageUrl: pageUrl ? displayUrl(pageUrl) : '' };
}
