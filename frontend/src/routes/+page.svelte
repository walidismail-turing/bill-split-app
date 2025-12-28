<script lang="ts">
	import { splitBill } from '$lib/api';
	import { formatMoney } from '$lib/money';
	import type { BillItem, Participant, SplitResponse, TipMode } from '$lib/types';
	import { env } from '$env/dynamic/public';

	const uid = () => crypto.randomUUID().slice(0, 8);

	let currency = $state('USD');

	let participants = $state<Participant[]>([
		{ id: uid(), name: 'Ava' },
		{ id: uid(), name: 'Ben' }
	]);

	let items = $state<BillItem[]>([
		{ id: uid(), name: 'Pizza', amount: '18.00', participants: [] },
		{ id: uid(), name: 'Soda', amount: '6.00', participants: [] }
	]);

	let totalBeforeTip = $state<string>('');

	let tipMode = $state<TipMode>('percent');
	let tipPercent = $state<string>('18.00');
	let tipFixed = $state<string>('0.00');

	let busy = $state(false);
	let error = $state<string | null>(null);
	let result = $state<SplitResponse | null>(null);
	let apiBaseShown = $derived(env.PUBLIC_API_BASE || '(same origin)');

	function toggleItemParticipant(itemId: string, participantId: string) {
		const item = items.find((i) => i.id === itemId);
		if (!item) return;

		const has = item.participants.includes(participantId);
		item.participants = has
			? item.participants.filter((p) => p !== participantId)
			: [...item.participants, participantId];
	}

	function addParticipant() {
		participants = [...participants, { id: uid(), name: `Guest ${participants.length + 1}` }];
	}

	function removeParticipant(id: string) {
		if (participants.length <= 1) return;
		participants = participants.filter((p) => p.id !== id);
		items = items.map((it) => ({ ...it, participants: it.participants.filter((pid) => pid !== id) }));
	}

	function addItem() {
		items = [...items, { id: uid(), name: `Item ${items.length + 1}`, amount: '0.00', participants: [] }];
	}

	function removeItem(id: string) {
		if (items.length <= 1) return;
		items = items.filter((i) => i.id !== id);
	}

	function validateForUi(): string | null {
		if (participants.length < 1) return 'Add at least one participant.';
		if (items.length < 1) return 'Add at least one item.';
		for (const p of participants) {
			if (!p.name.trim()) return 'Participant names cannot be empty.';
		}
		for (const it of items) {
			if (!it.name.trim()) return 'Item names cannot be empty.';
			if (Number.isNaN(Number(it.amount))) return `Item "${it.name}" has an invalid amount.`;
			if (Number(it.amount) < 0) return `Item "${it.name}" must be non-negative.`;
		}
		return null;
	}

	async function onSplit() {
		error = null;
		result = null;

		const uiErr = validateForUi();
		if (uiErr) {
			error = uiErr;
			return;
		}

		busy = true;
		try {
			result = await splitBill({
				currency,
				participants: participants.map((p) => ({ id: p.id, name: p.name.trim() })),
				items: items.map((i) => ({
					id: i.id,
					name: i.name.trim(),
					amount: (Number(i.amount) || 0).toFixed(2),
					participants: i.participants
				})),
				total_before_tip: totalBeforeTip.trim() ? Number(totalBeforeTip).toFixed(2) : null,
				tip_mode: tipMode,
				tip_percent: tipMode === 'percent' ? Number(tipPercent || 0).toFixed(2) : null,
				tip_fixed: tipMode === 'fixed' ? Number(tipFixed || 0).toFixed(2) : null
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Something went wrong.';
		} finally {
			busy = false;
		}
	}
</script>

<main class="min-h-screen">
	<div class="pointer-events-none fixed inset-0">
		<div
			class="absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-fuchsia-500/20 blur-3xl"
		></div>
		<div
			class="absolute -bottom-48 right-[-12rem] h-[520px] w-[520px] rounded-full bg-cyan-400/15 blur-3xl"
		></div>
	</div>

	<div class="relative mx-auto max-w-6xl px-4 py-10">
		<header class="mb-8 flex items-start justify-between gap-6">
			<div>
				<p class="text-xs font-medium tracking-widest text-slate-400">BILL SPLITTER</p>
				<h1 class="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
					Split the bill beautifully.
				</h1>
				<p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300">
					Add participants, itemize the bill, choose a tip (% or fixed), and get a rounding-safe breakdown
					instantly.
				</p>
			</div>

			<div class="hidden shrink-0 items-center gap-3 sm:flex">
				<label class="text-xs text-slate-300" for="currency-lg">Currency</label>
				<select
					id="currency-lg"
					class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none ring-0 focus:border-white/20"
					bind:value={currency}
				>
					<option value="USD">USD</option>
					<option value="EUR">EUR</option>
					<option value="GBP">GBP</option>
					<option value="CAD">CAD</option>
					<option value="AUD">AUD</option>
				</select>
			</div>
		</header>

		<div class="grid gap-6 lg:grid-cols-2">
			<section class="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-soft">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-base font-semibold text-white">Participants</h2>
					<button
						type="button"
						onclick={addParticipant}
						class="rounded-xl bg-white/10 px-3 py-2 text-sm font-medium text-white hover:bg-white/15 active:bg-white/10"
					>
						Add
					</button>
				</div>

				<div class="space-y-3">
					{#each participants as p (p.id)}
						<div class="flex items-center gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2">
							<div class="h-8 w-8 shrink-0 rounded-lg bg-gradient-to-br from-fuchsia-400/60 to-cyan-300/40"></div>
							<input
								class="w-full bg-transparent text-sm text-white placeholder:text-slate-500 focus:outline-none"
								bind:value={p.name}
								placeholder="Name"
							/>
							<button
								type="button"
								onclick={() => removeParticipant(p.id)}
								class="rounded-lg px-2 py-1 text-xs text-slate-300 hover:bg-white/10 hover:text-white disabled:opacity-40"
								disabled={participants.length <= 1}
								title="Remove"
							>
								Remove
							</button>
						</div>
					{/each}
				</div>
			</section>

			<section class="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-soft">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-base font-semibold text-white">Tip</h2>
					<div class="flex items-center gap-2">
						<button
							type="button"
							onclick={() => (tipMode = 'percent')}
							class={`rounded-xl px-3 py-2 text-sm font-medium ring-1 ring-white/10 hover:bg-white/10 ${tipMode === 'percent' ? 'bg-white/15' : ''}`}
						>
							%
						</button>
						<button
							type="button"
							onclick={() => (tipMode = 'fixed')}
							class={`rounded-xl px-3 py-2 text-sm font-medium ring-1 ring-white/10 hover:bg-white/10 ${tipMode === 'fixed' ? 'bg-white/15' : ''}`}
						>
							Fixed
						</button>
					</div>
				</div>

				<div class="grid gap-4 sm:grid-cols-2">
					<div class="space-y-1">
						<label class="text-xs text-slate-300" for="total-before-tip">Total before tip (optional)</label>
						<input
							id="total-before-tip"
							class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-white/20 focus:outline-none"
							inputmode="decimal"
							placeholder="Leave blank to use item subtotal"
							bind:value={totalBeforeTip}
						/>
						<p class="text-xs text-slate-500">
							Use this if your receipt total (pre-tip) includes tax/fees not itemized below.
						</p>
					</div>

					<div class="space-y-1">
						{#if tipMode === 'percent'}
							<label class="text-xs text-slate-300" for="tip-percent">Tip percent</label>
							<input
								id="tip-percent"
								class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-white/20 focus:outline-none"
								inputmode="decimal"
								bind:value={tipPercent}
								placeholder="18.00"
							/>
						{:else}
							<label class="text-xs text-slate-300" for="tip-fixed">Tip amount</label>
							<input
								id="tip-fixed"
								class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-white/20 focus:outline-none"
								inputmode="decimal"
								bind:value={tipFixed}
								placeholder="0.00"
							/>
						{/if}
						<p class="text-xs text-slate-500">Tip is distributed proportionally to each person’s pre-tip share.</p>
					</div>
				</div>
			</section>

			<section class="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-soft lg:col-span-2">
				<div class="mb-4 flex items-center justify-between gap-4">
					<h2 class="text-base font-semibold text-white">Items</h2>
					<div class="flex items-center gap-2">
						<div class="sm:hidden">
							<label class="sr-only" for="currency-sm">Currency</label>
							<select
								id="currency-sm"
								class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none ring-0 focus:border-white/20"
								bind:value={currency}
							>
								<option value="USD">USD</option>
								<option value="EUR">EUR</option>
								<option value="GBP">GBP</option>
								<option value="CAD">CAD</option>
								<option value="AUD">AUD</option>
							</select>
						</div>
						<button
							type="button"
							onclick={addItem}
							class="rounded-xl bg-white/10 px-3 py-2 text-sm font-medium text-white hover:bg-white/15 active:bg-white/10"
						>
							Add item
						</button>
					</div>
				</div>

				<div class="space-y-3">
					{#each items as it (it.id)}
						<div class="rounded-2xl border border-white/10 bg-black/20 p-4">
							<div class="grid gap-3 sm:grid-cols-[1.2fr_160px_auto] sm:items-center">
								<input
									class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-white/20 focus:outline-none"
									bind:value={it.name}
									placeholder="Item name"
								/>
								<div class="relative">
									<input
										class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-white/20 focus:outline-none"
										inputmode="decimal"
										bind:value={it.amount}
										placeholder="0.00"
									/>
								</div>
								<button
									type="button"
									onclick={() => removeItem(it.id)}
									class="justify-self-start rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-white/10 hover:text-white disabled:opacity-40"
									disabled={items.length <= 1}
								>
									Remove
								</button>
							</div>

							<div class="mt-3">
								<p class="mb-2 text-xs text-slate-400">
									Assigned to:
									<span class="text-slate-500">(leave empty to split among everyone)</span>
								</p>
								<div class="flex flex-wrap gap-2">
									{#each participants as p (p.id)}
										<button
											type="button"
											onclick={() => toggleItemParticipant(it.id, p.id)}
											class={`rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-white/10 transition ${
												it.participants.includes(p.id)
													? 'bg-white/15 text-white'
													: 'text-slate-300 hover:bg-white/10'
											}`}
										>
											{p.name || 'Unnamed'}
										</button>
									{/each}
								</div>
							</div>
						</div>
					{/each}
				</div>

				<div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
					{#if error}
						<div class="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
							{error}
						</div>
					{:else}
						<div class="text-xs text-slate-400">
							API base: <span class="font-mono text-slate-300">{apiBaseShown}</span>
						</div>
					{/if}

					<button
						type="button"
						onclick={onSplit}
						disabled={busy}
						class="rounded-2xl bg-gradient-to-r from-fuchsia-500 to-cyan-400 px-5 py-3 text-sm font-semibold text-black shadow-soft hover:brightness-110 disabled:opacity-60"
					>
						{busy ? 'Splitting…' : 'Split bill'}
					</button>
				</div>
			</section>
		</div>

		{#if result}
			<section class="mt-8 grid gap-6 lg:grid-cols-3">
				<div class="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-soft lg:col-span-1">
					<h3 class="text-sm font-semibold text-white">Summary</h3>
					<div class="mt-4 space-y-2 text-sm text-slate-200">
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Subtotal</span>
							<span>{formatMoney(result.subtotal, result.currency)}</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Adjustment</span>
							<span>{formatMoney(result.adjustment, result.currency)}</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Pre-tip total</span>
							<span>{formatMoney(result.total_before_tip, result.currency)}</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Tip</span>
							<span>{formatMoney(result.tip, result.currency)}</span>
						</div>
						<div class="mt-3 h-px bg-white/10"></div>
						<div class="flex items-center justify-between text-base font-semibold text-white">
							<span>Total</span>
							<span>{formatMoney(result.total_after_tip, result.currency)}</span>
						</div>
					</div>
				</div>

				<div class="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-soft lg:col-span-2">
					<h3 class="text-sm font-semibold text-white">Per person</h3>
					<div class="mt-4 grid gap-3 md:grid-cols-2">
						{#each result.participants as p (p.id)}
							<div class="rounded-2xl border border-white/10 bg-black/20 p-4">
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="text-sm font-semibold text-white">{p.name}</p>
										<p class="text-xs text-slate-400">
											Items {formatMoney(p.items, result.currency)} · Adj {formatMoney(p.adjustment, result.currency)} · Tip
											{formatMoney(p.tip, result.currency)}
										</p>
									</div>
									<div class="text-right">
										<p class="text-xs text-slate-400">Total</p>
										<p class="text-lg font-semibold text-white">{formatMoney(p.total, result.currency)}</p>
									</div>
								</div>

								{#if p.item_shares.length}
									<div class="mt-3 space-y-1">
										<p class="text-xs font-medium text-slate-300">Breakdown</p>
										<ul class="space-y-1 text-xs text-slate-300">
											{#each p.item_shares as s (s.item_id + s.item_name)}
												<li class="flex items-center justify-between">
													<span class="truncate pr-2 text-slate-400">{s.item_name}</span>
													<span class="shrink-0 text-slate-200">{formatMoney(s.amount, result.currency)}</span>
												</li>
											{/each}
										</ul>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</section>
		{/if}
	</div>
</main>
