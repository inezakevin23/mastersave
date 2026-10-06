from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    InvestmentAccount,
    InvestmentProduct,
    InvestmentRequest,
    InvestmentTransaction,
)
from .serializers import (
    InvestmentAccountSerializer,
    InvestmentProductSerializer,
    InvestmentRequestSerializer,
    InvestmentTransactionSerializer,
)
from .summary import get_grow_summary


class InvestmentProductListView(
    generics.ListAPIView
):
    serializer_class = (
        InvestmentProductSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentProduct.objects
            .filter(
                status=InvestmentProduct.Status.ACTIVE
            )
            .order_by("name")
        )


class InvestmentProductDetailView(
    generics.RetrieveAPIView
):
    serializer_class = (
        InvestmentProductSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return InvestmentProduct.objects.filter(
            status=InvestmentProduct.Status.ACTIVE
        )


class InvestmentRequestListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = (
        InvestmentRequestSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentRequest.objects
            .filter(
                scholar=self.request.user
            )
            .select_related(
                "product",
                "source_allocation",
            )
        )


class InvestmentRequestDetailView(
    generics.RetrieveAPIView
):
    serializer_class = (
        InvestmentRequestSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentRequest.objects
            .filter(
                scholar=self.request.user
            )
            .select_related(
                "product",
                "source_allocation",
            )
        )


class InvestmentAccountListView(
    generics.ListAPIView
):
    serializer_class = (
        InvestmentAccountSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentAccount.objects
            .filter(
                scholar=self.request.user
            )
            .select_related("product")
        )


class InvestmentAccountDetailView(
    generics.RetrieveAPIView
):
    serializer_class = (
        InvestmentAccountSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentAccount.objects
            .filter(
                scholar=self.request.user
            )
            .select_related("product")
        )


class InvestmentTransactionListView(
    generics.ListAPIView
):
    serializer_class = (
        InvestmentTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            InvestmentTransaction.objects
            .filter(
                account__scholar=self.request.user
            )
            .select_related("account", "account__product")
        )

class GrowSummaryView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        summary = get_grow_summary(
            request.user
        )

        return Response(
            {
                "success": True,
                "data": summary,
            }
        )
