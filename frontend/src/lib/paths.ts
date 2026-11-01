import { resolve } from '$app/paths';

const resolvePath = resolve as (path: string) => string;

export function href(path: string): string {
	return resolvePath(path);
}

export function basePath(): string {
	return href('/').replace(/\/$/, '');
}
