from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from rest_framework import serializers

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
    releases = AllowanceReleaseSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = AllowancePlan

        fields = [
            "id",
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
            "status",
            "releases",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        validate_plan_amounts(
            total_amount=attrs["total_amount"],
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