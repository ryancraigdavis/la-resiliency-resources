import type { ParamMatcher } from '@sveltejs/kit';
import { TOPIC_IDS } from '$lib/languages';

export const match = ((param: string) => TOPIC_IDS.includes(param)) satisfies ParamMatcher;
