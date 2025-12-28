import { env } from '$env/dynamic/public';
import type { SplitRequest, SplitResponse } from './types';

function apiBase() {
	// If unset, assume same-origin (useful if you front everything behind a gateway).
	return (env.PUBLIC_API_BASE || '').replace(/\/+$/, '');
}

export async function splitBill(payload: SplitRequest): Promise<SplitResponse> {
	const base = apiBase();
	const res = await fetch(`${base}/api/split/`, {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(payload)
	});

	if (!res.ok) {
		let detail: unknown = null;
		try {
			detail = await res.json();
		} catch {
			// ignore
		}
		throw new Error(
			`Split failed (${res.status}). ${detail ? JSON.stringify(detail) : 'Please check inputs.'}`
		);
	}
	return (await res.json()) as SplitResponse;
}

