from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


def money_to_cents(value: Decimal) -> int:
    quantized = value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def cents_to_money(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(TWOPLACES)


def allocate_evenly(amount_cents: int, bucket_ids: list[str]) -> dict[str, int]:
    """
    Split amount across buckets as evenly as possible, distributing any remainder
    deterministically by sorted bucket id.
    """
    if not bucket_ids:
        return {}
    base = amount_cents // len(bucket_ids)
    rem = amount_cents - base * len(bucket_ids)
    ordered = sorted(bucket_ids)
    out = {pid: base for pid in ordered}
    step = 1 if rem >= 0 else -1
    for i in range(abs(rem)):
        out[ordered[i % len(ordered)]] += step
    return out


def allocate_proportionally(amount_cents: int, weights_cents: dict[str, int]) -> dict[str, int]:
    """
    Allocate amount_cents across keys using weights (non-negative ints), ensuring
    the allocations sum exactly to amount_cents. Uses largest-remainder on
    fractional shares, ties broken deterministically by key.
    """
    keys = sorted(weights_cents.keys())
    if not keys:
        return {}

    total_weight = sum(max(0, w) for w in weights_cents.values())
    if total_weight <= 0:
        return allocate_evenly(amount_cents, keys)

    # Use integer math: floor( amount * w / total_weight )
    base_alloc: dict[str, int] = {}
    remainders: list[tuple[int, str]] = []
    used = 0
    for k in keys:
        w = max(0, weights_cents.get(k, 0))
        numerator = amount_cents * w
        q = int(numerator // total_weight)
        r = int(numerator - q * total_weight)  # remainder in "weight-units"
        base_alloc[k] = q
        used += q
        remainders.append((r, k))

    diff = amount_cents - used
    if diff == 0:
        return base_alloc

    # Distribute remaining cents by largest remainder; for negative diff,
    # subtract by smallest remainder (i.e., reverse).
    if diff > 0:
        remainders.sort(key=lambda t: (-t[0], t[1]))
        for i in range(diff):
            base_alloc[remainders[i % len(remainders)][1]] += 1
    else:
        remainders.sort(key=lambda t: (t[0], t[1]))
        for i in range(-diff):
            base_alloc[remainders[i % len(remainders)][1]] -= 1

    return base_alloc


@dataclass(frozen=True)
class SplitItemShare:
    item_id: str
    item_name: str
    cents: int


@dataclass(frozen=True)
class SplitParticipantResult:
    participant_id: str
    participant_name: str
    items_cents: int
    adjustment_cents: int
    pre_tip_cents: int
    tip_cents: int
    total_cents: int
    item_shares: list[SplitItemShare]


def split_bill(
    *,
    participants: list[dict],
    items: list[dict],
    total_before_tip: int | None,
    tip_mode: str,
    tip_value_cents: int,
    tip_percent_bp: int | None,
) -> dict:
    """
    Core splitting logic.

    Inputs are already validated and normalized:
    - total_before_tip is cents or None (derive from items)
    - tip_mode is "percent" or "fixed"
    - tip_value_cents used when mode=="fixed"
    - tip_percent_bp (basis points) used when mode=="percent" (e.g. 15% => 1500)
    """
    participant_ids = [p["id"] for p in participants]
    names_by_id = {p["id"]: p["name"] for p in participants}
    if not participant_ids:
        raise ValueError("participants required")

    # Item allocations
    item_shares_by_pid: dict[str, list[SplitItemShare]] = {pid: [] for pid in participant_ids}
    items_cents_by_pid: dict[str, int] = {pid: 0 for pid in participant_ids}

    subtotal_from_items = 0
    for item in items:
        cents = item["amount_cents"]
        subtotal_from_items += cents

        assigned = item["participants"] or participant_ids
        # if an item references unknown participant ids, ignore (validation should prevent)
        assigned = [pid for pid in assigned if pid in names_by_id]
        if not assigned:
            assigned = participant_ids

        alloc = allocate_evenly(cents, assigned)
        for pid, share_cents in alloc.items():
            items_cents_by_pid[pid] += share_cents
            item_shares_by_pid[pid].append(
                SplitItemShare(
                    item_id=item["id"],
                    item_name=item["name"],
                    cents=share_cents,
                )
            )

    subtotal = subtotal_from_items
    total_before_tip_cents = total_before_tip if total_before_tip is not None else subtotal

    # Adjustment (tax/fees/rounding differences) so that items sum can match entered total_before_tip.
    adjustment_total = total_before_tip_cents - subtotal
    adjustment_alloc = allocate_proportionally(adjustment_total, items_cents_by_pid)

    pre_tip_cents_by_pid = {
        pid: items_cents_by_pid[pid] + adjustment_alloc.get(pid, 0) for pid in participant_ids
    }

    # Tip
    if tip_mode == "percent":
        bp = tip_percent_bp or 0
        tip_amount = (total_before_tip_cents * bp) // 10000  # basis points
    else:
        tip_amount = tip_value_cents

    tip_alloc = allocate_proportionally(tip_amount, pre_tip_cents_by_pid)
    total_cents_by_pid = {pid: pre_tip_cents_by_pid[pid] + tip_alloc.get(pid, 0) for pid in participant_ids}

    results: list[SplitParticipantResult] = []
    for pid in participant_ids:
        results.append(
            SplitParticipantResult(
                participant_id=pid,
                participant_name=names_by_id[pid],
                items_cents=items_cents_by_pid[pid],
                adjustment_cents=adjustment_alloc.get(pid, 0),
                pre_tip_cents=pre_tip_cents_by_pid[pid],
                tip_cents=tip_alloc.get(pid, 0),
                total_cents=total_cents_by_pid[pid],
                item_shares=item_shares_by_pid[pid],
            )
        )

    return {
        "subtotal_cents": subtotal,
        "total_before_tip_cents": total_before_tip_cents,
        "adjustment_cents": adjustment_total,
        "tip_cents": tip_amount,
        "total_after_tip_cents": total_before_tip_cents + tip_amount,
        "participants": results,
    }

