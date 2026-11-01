import type { ParamMatcher } from '@sveltejs/kit';
import { LANG_CODES } from '$lib/languages';

export const match = ((param: string) => LANG_CODES.includes(param)) satisfies ParamMatcher;
