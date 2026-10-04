from django.db.models import Sum
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AllowancePlan, Expense
from .serializers import (
    AllowancePlanSerializer,
    ExpenseSerializer,
)
from .services import sync_releases


class AllowancePlanListCreateView(
    generics.ListCreateAPIView
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        sync_releases(instance)

        instance.refresh_from_db()

        return super().retrieve(
            request,
            *args,
            **kwargs,
        )


class ExpenseListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Expense.objects
            .filter(scholar=self.request.user)
            .select_related(
                "allowance_release",
                "allowance_release__plan",
            )
        )


class ExpenseDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(
            scholar=self.request.user
        )