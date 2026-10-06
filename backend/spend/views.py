from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AllowancePlan, AllowanceRelease
from .serializers import (
    AllowancePlanSerializer,
    AllowanceReleaseSerializer,
)


class AllowancePlanListView(
    generics.ListAPIView
):
    serializer_class = AllowancePlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AllowancePlan.objects
            .filter(scholar=self.request.user)
            .prefetch_related("releases")
        )


class AllowancePlanDetailView(
    generics.RetrieveAPIView
):
    serializer_class = AllowancePlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AllowancePlan.objects
            .filter(scholar=self.request.user)
            .prefetch_related("releases")
        )

class AllowanceReleaseListView(
    generics.ListAPIView
):
    serializer_class = AllowanceReleaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AllowanceRelease.objects
            .filter(
                plan__scholar=self.request.user
            )
            .select_related("plan")
            .order_by("week_number")
        )


class AllowanceReleaseDetailView(
    generics.RetrieveAPIView
):
    serializer_class = AllowanceReleaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AllowanceRelease.objects
            .filter(
                plan__scholar=self.request.user
            )
            .select_related("plan")
        )


