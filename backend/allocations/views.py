from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import get_setup_status
from .models import DepositAllocation
from .serializers import (
    AllocationSetupResponseSerializer,
    AllocationSetupSerializer,
    DepositAllocationSerializer,
    AllocationSetupStatusSerializer,
)


class AllocationSetupView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):
        serializer = AllocationSetupSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        setup = serializer.save()

        response_serializer = (
            AllocationSetupResponseSerializer(
                setup
            )
        )

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class AllocationListView(
    generics.ListAPIView
):
    serializer_class = (
        DepositAllocationSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

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
    serializer_class = (
        DepositAllocationSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            DepositAllocation.objects
            .filter(
                deposit__scholar=self.request.user
            )
            .select_related("deposit")
        )

class AllocationSetupStatusView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        status_data = get_setup_status(
            request.user
        )

        serializer = (
            AllocationSetupStatusSerializer(
                status_data
            )
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            }
        )