from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_allocation_amounts(
    deposit_amount,
    spend_amount,
    save_amount,
    grow_amount,
):
    deposit_amount = Decimal(deposit_amount)
    spend_amount = Decimal(spend_amount)
    save_amount = Decimal(save_amount)
    grow_amount = Decimal(grow_amount)

    if (
        spend_amount < 0
        or save_amount < 0
        or grow_amount < 0
    ):
        raise ValidationError(
            "Allocation amounts cannot be negative."
        )

    total = (
        spend_amount
        + save_amount
        + grow_amount
    )

    if total != deposit_amount:
        raise ValidationError(
            {
                "allocation": (
                    "Spend, Save and Grow must "
                    "add up exactly to the deposit amount."
                )
            }
        )