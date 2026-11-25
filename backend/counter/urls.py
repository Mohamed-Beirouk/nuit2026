from django.urls import path

from .views import ClaimListCreateView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("claims/", ClaimListCreateView.as_view(), name="claims"),
]
