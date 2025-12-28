export type Participant = { id: string; name: string };
export type BillItem = { id: string; name: string; amount: string; participants: string[] };

export type TipMode = 'percent' | 'fixed';

export type SplitRequest = {
	currency: string;
	participants: Participant[];
	items: Array<{ id: string; name: string; amount: string; participants?: string[] }>;
	total_before_tip?: string | null;
	tip_mode: TipMode;
	tip_percent?: string | null;
	tip_fixed?: string | null;
};

export type SplitResponse = {
	currency: string;
	subtotal: string;
	total_before_tip: string;
	adjustment: string;
	tip: string;
	total_after_tip: string;
	participants: Array<{
		id: string;
		name: string;
		items: string;
		adjustment: string;
		pre_tip: string;
		tip: string;
		total: string;
		item_shares: Array<{ item_id: string; item_name: string; amount: string }>;
	}>;
};

