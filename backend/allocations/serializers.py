from django.core.exceptions import ValidationError

from rest_framework import serializers

from deposits.models import Deposit

from .models import DepositAllocation
from .validators import validate_allocation_amounts


class DepositAllocationSerializer(
    serializers.ModelSerializer
):
    deposit = serializers.PrimaryKeyRelatedField(
        queryset=Deposit.objects.all()
    )

    total_allocated = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )

    class Meta:
        model = DepositAllocation

        fields = [
            "id",
            "deposit",
            "spend_amount",
            "save_amount",
            "grow_amount",
            "total_allocated",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "total_allocated",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_deposit(self, deposit):
        request = self.context["request"]

        if deposit.scholar_id != request.user.id:
            raise serializers.ValidationError(
                "This deposit does not belong to you."
            )

        if deposit.status != Deposit.Status.SUCCESSFUL:
            raise serializers.ValidationError(
                "Only successful deposits can be allocated."
            )

        if hasattr(deposit, "allocation"):
            raise serializers.ValidationError(
                "This deposit has already been allocated."
            )

        return deposit

    def validate(self, attrs):
        deposit = attrs["deposit"]

        validate_allocation_amounts(
            deposit_amount=deposit.amount,
            spend_amount=attrs["spend_amount"],
            save_amount=attrs["save_amount"],
            grow_amount=attrs["grow_amount"],
        )

        return attrs