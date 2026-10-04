from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import DepositAllocation
from .serializers import DepositAllocationSerializer


class AllocationListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = DepositAllocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            DepositAllocation.objects
            .filter(
                deposit__scholar=self.request.user
            )
            .select_related("deposit")
        )


class AllocationDetailView(
    generics.RetrieveAPIView
):
    serializer_class = DepositAllocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            DepositAllocation.objects
            .filter(
                deposit__scholar=self.request.user
            )
            .select_related("deposit")
        )