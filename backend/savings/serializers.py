from django.db.models import Sum

from rest_framework import serializers

from allocations.models import DepositAllocation

from .models import (
    SavingsBucket,
    SavingsTransaction,
)
from .services import (
    create_contribution,
    create_withdrawal,
    get_bucket_balance,
)
from .validators import validate_goal_bucket


class SavingsTransactionSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = SavingsTransaction

        fields = [
            "id",
            "transaction_type",
            "amount",
            "reference",
            "description",
            "status",
            "confirmed_at",
            "created_at",
        ]

        read_only_fields = fields


class SavingsBucketSerializer(
    serializers.ModelSerializer
):
    balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )

    remaining_to_target = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        allow_null=True,
        read_only=True,
    )

    progress_percentage = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        read_only=True,
    )

    is_locked = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = SavingsBucket

        fields = [
            "id",
            "name",
            "bucket_type",
            "target_amount",
            "target_date",
            "status",
            "balance",
            "remaining_to_target",
            "progress_percentage",
            "is_locked",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "balance",
            "remaining_to_target",
            "progress_percentage",
            "is_locked",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        validate_goal_bucket(
            bucket_type=attrs.get(
                "bucket_type",
                self.instance.bucket_type
                if self.instance
                else None,
            ),
            target_amount=attrs.get(
                "target_amount",
                self.instance.target_amount
                if self.instance
                else None,
            ),
        )

        return attrs

    def create(self, validated_data):
        return SavingsBucket.objects.create(
            scholar=self.context[
                "request"
            ].user,
            **validated_data,
        )


class SavingsContributionSerializer(
    serializers.Serializer
):
    allocation = serializers.PrimaryKeyRelatedField(
        queryset=DepositAllocation.objects.all()
    )

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=1,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )


class SavingsWithdrawalSerializer(
    serializers.Serializer
):
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=1,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )