from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from rest_framework import serializers

from allocations.models import DepositAllocation

from .models import (
    AllowancePlan,
    AllowanceRelease,
    Expense,
)
from .services import create_allowance_releases
from .validators import (
    validate_expense_does_not_exceed_budget,
    validate_plan_amounts,
)


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


class ExpenseSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Expense

        fields = [
            "id",
            "allowance_release",
            "category",
            "amount",
            "description",
            "spent_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        scholar = request.user

        release = attrs["allowance_release"]

        if release.plan.scholar_id != scholar.id:
            raise serializers.ValidationError(
                {
                    "allowance_release": (
                        "This allowance release "
                        "does not belong to you."
                    )
                }
            )

        if release.status != (
            release.Status.RELEASED
        ):
            raise serializers.ValidationError(
                {
                    "allowance_release": (
                        "This allowance release "
                        "is not currently available."
                    )
                }
            )

        already_spent = (
            release.expenses.aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        validate_expense_does_not_exceed_budget(
            expense_amount=attrs["amount"],
            already_spent=already_spent,
            weekly_budget=release.amount,
        )

        return attrs

    def create(self, validated_data):
        return Expense.objects.create(
            scholar=self.context[
                "request"
            ].user,
            **validated_data,
        )