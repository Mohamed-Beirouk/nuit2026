from django.db import OperationalError, connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Claim, Counter
from .serializers import ClaimSerializer
from .writer import claim_writer


class HealthView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            stored = Counter.objects.filter(pk=1).values_list("value", flat=True).first()
        except OperationalError:
            return Response(
                {"status": "unavailable", "database": "locked"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "status": "ok",
                "database": "ok",
                "counter": 0 if stored is None else stored,
            }
        )


class ClaimListCreateView(APIView):
    def get(self, request):
        stored = Counter.objects.filter(pk=1).values_list("value", flat=True).first()
        claims = Claim.objects.order_by("-number")[:100]
        return Response(
            {
                "counter": 0 if stored is None else stored,
                "claims": ClaimSerializer(claims, many=True).data,
            }
        )

    def post(self, request):
        raw = request.data.get("name", "")
        name = raw.strip() if isinstance(raw, str) else ""
        if not name:
            return Response(
                {"detail": "Name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(name) > 80:
            return Response(
                {"detail": "Name must be 80 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Drop this request's connection before waiting, so a read opened by
        # middleware cannot sit on a SQLite lock while the writer runs.
        connection.close()
        try:
            claim = claim_writer.submit(name)
        except (TimeoutError, OperationalError):
            return Response(
                {"detail": "The counter is busy. Try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(claim, status=status.HTTP_201_CREATED)
