from rest_framework import serializers

from allocations.models import DepositAllocation

from .models import (
    AllowancePlan,
    AllowanceRelease,
)
from .services import create_allowance_releases
from .validators import validate_plan_amounts


class AllowanceReleaseSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = AllowanceRelease

        fields = [
            "id",
            "week_number",
            "amount",
            "scheduled_at",
            "released_at",
            "status",
            "provider",
            "provider_reference",
            "failure_reason",
        ]

        read_only_fields = fields


class AllowancePlanSerializer(
    serializers.ModelSerializer
):
    source_allocation = serializers.PrimaryKeyRelatedField(
        queryset=DepositAllocation.objects.all(),
        write_only=True,
    )
    total_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )
    releases = AllowanceReleaseSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = AllowancePlan

        fields = [
            "id",
            "source_allocation",
            "total_amount",
            "weekly_amount",
            "number_of_weeks",
            "start_date",
            "release_weekday",
            "release_time",
            "status",
            "releases",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "total_amount",
            "status",
            "releases",
            "created_at",
            "updated_at",
        ]

    def validate_source_allocation(
        self,
        allocation,
    ):
        request = self.context["request"]

        if allocation.deposit.scholar_id != (
            request.user.id
        ):
            raise serializers.ValidationError(
                "This allocation does not belong to you."
            )

        if allocation.status != (
            DepositAllocation.Status.CONFIRMED
        ):
            raise serializers.ValidationError(
                "This allocation is not available."
            )

        if allocation.spend_amount <= 0:
            raise serializers.ValidationError(
                "The Spend allocation must be greater than zero."
            )

        if hasattr(allocation, "spend_plan"):
            raise serializers.ValidationError(
                "This Spend allocation already has an allowance plan."
            )

        return allocation

    def validate(self, attrs):
        allocation = attrs["source_allocation"]

        validate_plan_amounts(
            allocation_amount=allocation.spend_amount,
            weekly_amount=attrs["weekly_amount"],
            number_of_weeks=attrs[
                "number_of_weeks"
            ],
        )

        return attrs

    def create(self, validated_data):
        scholar = self.context[
            "request"
        ].user

        plan = AllowancePlan.objects.create(
            scholar=scholar,
            status=AllowancePlan.Status.ACTIVE,
            **validated_data,
        )

        create_allowance_releases(plan)

        return plan


