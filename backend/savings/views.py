from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from allocations.models import DepositAllocation

from .models import SavingsBucket, SavingsTransaction
from .serializers import (
    SavingsBucketSerializer,
    SavingsContributionSerializer,
    SavingsTransactionSerializer,
    SavingsWithdrawalSerializer,
)
from .services import (
    create_contribution,
    create_withdrawal,
)


class SavingsBucketListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = SavingsBucketSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            SavingsBucket.objects
            .filter(
                scholar=self.request.user
            )
            .prefetch_related("transactions")
        )


class SavingsBucketDetailView(
    generics.RetrieveAPIView
):
    serializer_class = SavingsBucketSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            SavingsBucket.objects
            .filter(
                scholar=self.request.user
            )
            .prefetch_related("transactions")
        )


class SavingsContributionView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):
        bucket = get_object_or_404(
            SavingsBucket,
            pk=pk,
            scholar=request.user,
        )

        serializer = (
            SavingsContributionSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        allocation = (
            serializer.validated_data[
                "allocation"
            ]
        )

        if allocation.deposit.scholar_id != (
            request.user.id
        ):
            return Response(
                {
                    "success": False,
                    "error": (
                        "This allocation does "
                        "not belong to you."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        transaction_record = create_contribution(
            bucket=bucket,
            allocation=allocation,
            amount=serializer.validated_data[
                "amount"
            ],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
        )

        return Response(
            {
                "success": True,
                "data": (
                    SavingsTransactionSerializer(
                        transaction_record
                    ).data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class SavingsWithdrawalView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):
        bucket = get_object_or_404(
            SavingsBucket,
            pk=pk,
            scholar=request.user,
        )

        serializer = (
            SavingsWithdrawalSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        transaction_record = create_withdrawal(
            bucket=bucket,
            amount=serializer.validated_data[
                "amount"
            ],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
        )

        return Response(
            {
                "success": True,
                "data": (
                    SavingsTransactionSerializer(
                        transaction_record
                    ).data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class SavingsTransactionListView(
    generics.ListAPIView
):
    serializer_class = (
        SavingsTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            SavingsTransaction.objects
            .filter(
                bucket__scholar=self.request.user
            )
            .select_related("bucket")
        )