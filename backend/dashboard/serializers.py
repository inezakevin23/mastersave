from rest_framework import serializers


class SpendDashboardSerializer(
    serializers.Serializer
):
    total_allocated = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
    )

    current_week = serializers.IntegerField(
        allow_null=True,
    )

    total_weeks = serializers.IntegerField(
        allow_null=True,
    )

    weekly_budget = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        allow_null=True,
    )

    used_this_week = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        allow_null=True,
    )

    remaining_this_week = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        allow_null=True,
    )

    next_release = serializers.DateTimeField(
        allow_null=True,
    )