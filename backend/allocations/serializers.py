from rest_framework import serializers

from savings.serializers import (
    SavingsBucketSerializer,
)
from spend.serializers import (
    AllowancePlanSerializer,
)

from deposits.models import Deposit

from .models import DepositAllocation
from .services import setup_allocation


class DepositAllocationSerializer(
    serializers.ModelSerializer
):
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

        read_only_fields = fields


class AllocationSetupSerializer(
    serializers.Serializer
):
    deposit = serializers.PrimaryKeyRelatedField(
        queryset=Deposit.objects.all()
    )

    spend_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=0,
    )

    save_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=0,
    )

    grow_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=0,
    )

    weekly_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=1,
    )

    number_of_weeks = serializers.IntegerField(
        min_value=1,
        max_value=52,
    )

    start_date = serializers.DateField()

    release_weekday = serializers.IntegerField(
        min_value=0,
        max_value=6,
    )

    release_time = serializers.TimeField()

    goal_lock_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=0,
    )

    goal_lock_target_amount = (
        serializers.DecimalField(
            max_digits=14,
            decimal_places=0,
            min_value=1,
        )
    )

    goal_lock_target_date = (
        serializers.DateField(
            required=False,
            allow_null=True,
        )
    )

    emergency_save_amount = (
        serializers.DecimalField(
            max_digits=14,
            decimal_places=0,
            min_value=0,
        )
    )

    goal_lock_name = serializers.CharField(
        max_length=100,
        required=False,
        default="Goal Lock",
    )

    emergency_save_name = serializers.CharField(
        max_length=100,
        required=False,
        default="Emergency Save",
    )

    def validate(self, attrs):
        request = self.context["request"]
        deposit = attrs["deposit"]

        if deposit.scholar_id != request.user.id:
            raise serializers.ValidationError(
                {
                    "deposit": (
                        "This deposit does "
                        "not belong to you."
                    )
                }
            )

        expected_weekly_total = (
            attrs["weekly_amount"]
            * attrs["number_of_weeks"]
        )

        if (
            expected_weekly_total
            != attrs["spend_amount"]
        ):
            raise serializers.ValidationError(
                {
                    "weekly_amount": (
                        "Weekly amount multiplied "
                        "by number of weeks must equal "
                        "the Spend allocation."
                    )
                }
            )

        if (
            attrs["goal_lock_amount"]
            + attrs["emergency_save_amount"]
            != attrs["save_amount"]
        ):
            raise serializers.ValidationError(
                {
                    "save": (
                        "Goal Lock amount plus "
                        "Emergency Save amount must "
                        "equal the Save allocation."
                    )
                }
            )

        if (
            attrs["goal_lock_target_amount"]
            < attrs["goal_lock_amount"]
        ):
            raise serializers.ValidationError(
                {
                    "goal_lock_target_amount": (
                        "Goal Lock target must be "
                        "at least its initial amount."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        return setup_allocation(
            scholar=self.context[
                "request"
            ].user,
            **validated_data,
        )


class AllocationSetupResponseSerializer(
    serializers.Serializer
):
    allocation = serializers.SerializerMethodField()
    plan = AllowancePlanSerializer()
    goal_bucket = SavingsBucketSerializer(
        allow_null=True
    )
    emergency_bucket = SavingsBucketSerializer(
        allow_null=True
    )

    def get_allocation(self, obj):
        allocation = obj["allocation"]

        return {
            "id": str(allocation.id),
            "deposit": str(
                allocation.deposit_id
            ),
            "spend_amount": (
                allocation.spend_amount
            ),
            "save_amount": (
                allocation.save_amount
            ),
            "grow_amount": (
                allocation.grow_amount
            ),
            "total_allocated": (
                allocation.total_allocated
            ),
            "status": allocation.status,
        }

class AllocationSetupStatusSerializer(
    serializers.Serializer
):
    setup_complete = serializers.BooleanField()

    has_successful_deposit = (
        serializers.BooleanField()
    )

    has_unallocated_deposit = (
        serializers.BooleanField()
    )

    latest_deposit_id = (
        serializers.CharField(
            allow_null=True
        )
    )

    allocation_id = (
        serializers.CharField(
            allow_null=True
        )
    )

    spend = serializers.DictField()

    save = serializers.DictField()

    grow = serializers.DictField()