from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_plan_amounts(
    allocation_amount,
    weekly_amount,
    number_of_weeks,
):
    allocation_amount = Decimal(
        allocation_amount
    )

    weekly_amount = Decimal(
        weekly_amount
    )

    expected_total = (
        weekly_amount * number_of_weeks
    )

    if allocation_amount != expected_total:
        raise ValidationError(
            {
                "weekly_amount": (
                    "Weekly amount multiplied by "
                    "number of weeks must equal "
                    "the Spend allocation."
                )
            }
        )