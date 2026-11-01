// Scheme and host of the live site, with no path (BASE_PATH supplies any path). Used for the QR
// code on printed flyers and for language alternate links.
export const SITE_URL = 'https://ryancraigdavis.github.io';

// Google Form for "Report a problem". Use a prefilled link and put {id} where the resource id goes,
// e.g. 'https://docs.google.com/forms/d/e/FORM_ID/viewform?usp=pp_url&entry.123456={id}'.
export const REPORT_URL = '';

// Resources shown in the "Need help now?" strip, with the UI text key that introduces each.
export const EMERGENCY = [
	{ id: '211-la', textKey: 'emergency_211', sms: true },
	{ id: 'larrn', textKey: 'emergency_detained', sms: false }
] as const;
