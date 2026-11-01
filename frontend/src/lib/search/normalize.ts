const CHARACTER_FOLDS: Record<string, string> = {
	ı: 'i',
	ي: 'ی',
	ى: 'ی',
	ك: 'ک',
	ة: 'ه',
	ۀ: 'ه',
	أ: 'ا',
	إ: 'ا',
	آ: 'ا',
	ؤ: 'و',
	'‌': ' ',
	'ـ': ''
};

const FOLDABLE = new RegExp(`[${Object.keys(CHARACTER_FOLDS).join('')}]`, 'g');
const EASTERN_DIGITS = /[٠-٩۰-۹]/g;
const COMBINING_MARKS = /\p{M}+/gu;

function westernDigit(digit: string): string {
	const code = digit.charCodeAt(0);
	return String(code >= 0x06f0 ? code - 0x06f0 : code - 0x0660);
}

export function normalize(text: string): string {
	return text
		.normalize('NFKC')
		.toLowerCase()
		.normalize('NFD')
		.replace(COMBINING_MARKS, '')
		.normalize('NFC')
		.replace(FOLDABLE, (char) => CHARACTER_FOLDS[char])
		.replace(EASTERN_DIGITS, westernDigit);
}
