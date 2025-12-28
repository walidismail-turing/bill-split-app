export function formatMoney(amount: string | number, currency: string) {
	const value = typeof amount === 'string' ? Number(amount) : amount;
	return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value);
}

