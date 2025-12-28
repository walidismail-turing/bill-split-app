from django.urls import path

from .views import HealthzView, SplitBillView

urlpatterns = [
    path("healthz/", HealthzView.as_view(), name="healthz"),
    path("split/", SplitBillView.as_view(), name="split"),
]

