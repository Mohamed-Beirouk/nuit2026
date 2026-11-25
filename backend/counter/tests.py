from concurrent.futures import ThreadPoolExecutor

from django.db import OperationalError
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from .models import Claim, Counter


class ClaimApiTests(TransactionTestCase):
    def test_health_reports_database_and_counter(self):
        response = APIClient().get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["counter"], 0)

    def test_counter_starts_at_zero(self):
        response = APIClient().get("/api/claims/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["counter"], 0)
        self.assertEqual(response.data["claims"], [])

    def test_click_saves_the_next_number_for_that_name(self):
        client = APIClient()
        first = client.post("/api/claims/", {"name": "beirouk"}, format="json")
        second = client.post("/api/claims/", {"name": "amina"}, format="json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["name"], "beirouk")
        self.assertEqual(first.data["number"], 1)
        self.assertEqual(second.data["name"], "amina")
        self.assertEqual(second.data["number"], 2)
        self.assertEqual(Counter.objects.get(pk=1).value, 2)
        self.assertEqual(Claim.objects.count(), 2)

    def test_blank_name_is_rejected_and_does_not_increment(self):
        response = APIClient().post("/api/claims/", {"name": "   "}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Claim.objects.count(), 0)
        stored = Counter.objects.filter(pk=1).values_list("value", flat=True).first()
        self.assertEqual(0 if stored is None else stored, 0)

    def test_same_name_can_take_another_number_on_the_next_click(self):
        client = APIClient()
        first = client.post("/api/claims/", {"name": "beirouk"}, format="json")
        second = client.post("/api/claims/", {"name": "beirouk"}, format="json")
        self.assertEqual(first.data["number"], 1)
        self.assertEqual(second.data["number"], 2)

    def test_overlapping_clicks_get_unique_numbers_without_lock_errors(self):
        names = [f"person-{i}" for i in range(40)]

        def claim(name):
            response = APIClient().post("/api/claims/", {"name": name}, format="json")
            if response.status_code != 201:
                raise AssertionError(response.status_code, response.content)
            return response.data["number"]

        with ThreadPoolExecutor(max_workers=12) as pool:
            try:
                numbers = list(pool.map(claim, names))
            except OperationalError as exc:
                self.fail(f"SQLite lock error: {exc}")

        self.assertEqual(sorted(numbers), list(range(1, 41)))
        self.assertEqual(Counter.objects.get(pk=1).value, 40)
        self.assertEqual(Claim.objects.count(), 40)
