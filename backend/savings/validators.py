from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_goal_bucket(
    bucket_type,
    target_amount,
):
    if bucket_type == "GOAL_LOCK":
        if target_amount is None:
            raise ValidationError(
                {
                    "target_amount": (
                        "Goal Lock requires a target amount."
                    )
                }
            )

        if Decimal(target_amount) <= 0:
            raise ValidationError(
                {
                    "target_amount": (
                        "Target amount must be greater than zero."
                    )
                }
            )


def validate_contribution_amount(
    amount,
    remaining_allocation,
):
    amount = Decimal(amount)
    remaining_allocation = Decimal(
        remaining_allocation
    )

    if amount <= 0:
        raise ValidationError(
            {
                "amount": (
                    "Contribution must be greater than zero."
                )
            }
        )

    if amount > remaining_allocation:
        raise ValidationError(
            {
                "amount": (
                    "Contribution exceeds the "
                    f"remaining Save allocation of "
                    f"{remaining_allocation} RWF."
                )
            }
        )


def validate_withdrawal_amount(
    amount,
    available_balance,
):
    amount = Decimal(amount)
    available_balance = Decimal(
        available_balance
    )

    if amount <= 0:
        raise ValidationError(
            {
                "amount": (
                    "Withdrawal must be greater than zero."
                )
            }
        )

    if amount > available_balance:
        raise ValidationError(
            {
                "amount": (
                    "Withdrawal exceeds the "
                    f"available balance of "
                    f"{available_balance} RWF."
                )
            }
        )


def validate_bucket_withdrawal(
    bucket_type,
    balance,
    target_amount,
):
    if bucket_type == "GOAL_LOCK":
        if target_amount is None:
            raise ValidationError(
                "Goal Lock has no target amount."
            )

        if Decimal(balance) < Decimal(
            target_amount
        ):
            raise ValidationError(
                {
                    "bucket": (
                        "Goal Lock is locked until "
                        "the target is reached."
                    )
                }
            )