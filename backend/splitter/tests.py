from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase


class SplitApiTests(APITestCase):
    def test_split_percent_tip_sums_correctly(self):
        payload = {
            "currency": "USD",
            "participants": [{"id": "a", "name": "Ava"}, {"id": "b", "name": "Ben"}],
            "items": [
                {"id": "i1", "name": "Pizza", "amount": "10.00", "participants": ["a", "b"]},
                {"id": "i2", "name": "Soda", "amount": "5.00", "participants": ["a"]},
            ],
            "tip_mode": "percent",
            "tip_percent": "10.00",
        }
        res = self.client.post(reverse("split"), payload, format="json")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["subtotal"], "15.00")
        self.assertEqual(data["total_before_tip"], "15.00")
        self.assertEqual(data["tip"], "1.50")
        self.assertEqual(data["total_after_tip"], "16.50")

        totals = [Decimal(p["total"]) for p in data["participants"]]
        self.assertEqual(sum(totals), Decimal("16.50"))

    def test_split_fixed_tip_and_total_before_tip_adjustment(self):
        payload = {
            "currency": "USD",
            "participants": [{"id": "a", "name": "Ava"}, {"id": "b", "name": "Ben"}],
            "items": [
                {"id": "i1", "name": "Item", "amount": "9.99", "participants": ["a", "b"]},
            ],
            # e.g. tax/fees not included in itemization
            "total_before_tip": "10.99",
            "tip_mode": "fixed",
            "tip_fixed": "1.01",
        }
        res = self.client.post(reverse("split"), payload, format="json")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["subtotal"], "9.99")
        self.assertEqual(data["total_before_tip"], "10.99")
        self.assertEqual(data["tip"], "1.01")
        self.assertEqual(data["total_after_tip"], "12.00")

        totals = [Decimal(p["total"]) for p in data["participants"]]
        self.assertEqual(sum(totals), Decimal("12.00"))
