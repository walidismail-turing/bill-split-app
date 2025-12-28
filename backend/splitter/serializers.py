from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .services import cents_to_money, money_to_cents, split_bill


class ParticipantSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)


class ItemSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    participants = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
    )


class SplitRequestSerializer(serializers.Serializer):
    currency = serializers.CharField(required=False, default="USD", max_length=8)
    participants = ParticipantSerializer(many=True)
    items = ItemSerializer(many=True, required=False, default=list)

    # Optional override for "pre-tip total" (e.g. includes tax/fees not in itemization).
    total_before_tip = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0.00")
    )

    tip_mode = serializers.ChoiceField(choices=["percent", "fixed"], default="percent")
    tip_percent = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0.00")
    )
    tip_fixed = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0.00")
    )

    def validate(self, attrs):
        participants = attrs.get("participants") or []
        if not participants:
            raise serializers.ValidationError({"participants": "At least one participant is required."})

        ids = [p["id"] for p in participants]
        if len(set(ids)) != len(ids):
            raise serializers.ValidationError({"participants": "Participant ids must be unique."})

        items = attrs.get("items") or []
        item_ids = [i["id"] for i in items]
        if len(set(item_ids)) != len(item_ids):
            raise serializers.ValidationError({"items": "Item ids must be unique."})

        valid_ids = set(ids)
        for item in items:
            for pid in item.get("participants") or []:
                if pid not in valid_ids:
                    raise serializers.ValidationError(
                        {"items": f"Item '{item['id']}' references unknown participant id '{pid}'."}
                    )

        tip_mode = attrs.get("tip_mode", "percent")
        if tip_mode == "percent":
            if attrs.get("tip_fixed") not in (None, Decimal("0.00")):
                # allow but ignore; keep strict to prevent confusion
                raise serializers.ValidationError({"tip_fixed": "Do not send tip_fixed when tip_mode=percent."})
            tip_percent = attrs.get("tip_percent")
            if tip_percent is None:
                attrs["tip_percent"] = Decimal("0.00")
        else:
            if attrs.get("tip_percent") not in (None, Decimal("0.00")):
                raise serializers.ValidationError({"tip_percent": "Do not send tip_percent when tip_mode=fixed."})
            tip_fixed = attrs.get("tip_fixed")
            if tip_fixed is None:
                attrs["tip_fixed"] = Decimal("0.00")

        return attrs

    def create(self, validated_data):
        # not used
        return validated_data


class SplitResponseParticipantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    items = serializers.DecimalField(max_digits=12, decimal_places=2)
    adjustment = serializers.DecimalField(max_digits=12, decimal_places=2)
    pre_tip = serializers.DecimalField(max_digits=12, decimal_places=2)
    tip = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    item_shares = serializers.ListField(child=serializers.DictField(), required=True)


class SplitResponseSerializer(serializers.Serializer):
    currency = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_before_tip = serializers.DecimalField(max_digits=12, decimal_places=2)
    adjustment = serializers.DecimalField(max_digits=12, decimal_places=2)
    tip = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_after_tip = serializers.DecimalField(max_digits=12, decimal_places=2)
    participants = SplitResponseParticipantSerializer(many=True)


def compute_split_response(validated: dict) -> dict:
    currency = validated.get("currency", "USD")
    participants = validated["participants"]
    items = validated.get("items") or []

    total_before_tip = validated.get("total_before_tip")
    total_before_tip_cents = money_to_cents(total_before_tip) if total_before_tip is not None else None

    tip_mode = validated.get("tip_mode", "percent")
    tip_fixed = validated.get("tip_fixed") or Decimal("0.00")
    tip_fixed_cents = money_to_cents(tip_fixed)

    tip_percent = validated.get("tip_percent") or Decimal("0.00")
    # basis points (two decimals): 15.25% => 1525 bp
    tip_percent_bp = int((tip_percent * 100).quantize(Decimal("1")))

    normalized_items = []
    for item in items:
        normalized_items.append(
            {
                "id": item["id"],
                "name": item["name"],
                "amount_cents": money_to_cents(item["amount"]),
                "participants": item.get("participants") or [],
            }
        )

    result = split_bill(
        participants=participants,
        items=normalized_items,
        total_before_tip=total_before_tip_cents,
        tip_mode=tip_mode,
        tip_value_cents=tip_fixed_cents,
        tip_percent_bp=tip_percent_bp,
    )

    return {
        "currency": currency,
        "subtotal": cents_to_money(result["subtotal_cents"]),
        "total_before_tip": cents_to_money(result["total_before_tip_cents"]),
        "adjustment": cents_to_money(result["adjustment_cents"]),
        "tip": cents_to_money(result["tip_cents"]),
        "total_after_tip": cents_to_money(result["total_after_tip_cents"]),
        "participants": [
            {
                "id": p.participant_id,
                "name": p.participant_name,
                "items": cents_to_money(p.items_cents),
                "adjustment": cents_to_money(p.adjustment_cents),
                "pre_tip": cents_to_money(p.pre_tip_cents),
                "tip": cents_to_money(p.tip_cents),
                "total": cents_to_money(p.total_cents),
                "item_shares": [
                    {"item_id": s.item_id, "item_name": s.item_name, "amount": cents_to_money(s.cents)}
                    for s in p.item_shares
                ],
            }
            for p in result["participants"]
        ],
    }

