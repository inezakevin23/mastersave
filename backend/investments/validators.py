from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_investment_amount(
    amount,
    minimum_amount,
):
    amount = Decimal(amount)
    minimum_amount = Decimal(minimum_amount)

    if amount < minimum_amount:
        raise ValidationError(
            {
                "amount": (
                    f"Minimum investment amount "
                    f"is {minimum_amount} RWF."
                )
            }
        )


def validate_request_against_grow_allocation(
    amount,
    available_grow_amount,
):
    amount = Decimal(amount)
    available_grow_amount = Decimal(
        available_grow_amount
    )

    if amount > available_grow_amount:
        raise ValidationError(
            {
                "amount": (
                    "Investment amount exceeds the "
                    f"available Grow allocation of "
                    f"{available_grow_amount} RWF."
                )
            }
        )


def validate_transaction_account_ownership(
    account,
    scholar,
):
    if account.scholar_id != scholar.id:
        raise ValidationError(
            {
                "account": (
                    "This investment account "
                    "does not belong to you."
                )
            }
        )