from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_plan_amounts(
    total_amount,
    weekly_amount,
    number_of_weeks,
):
    total_amount = Decimal(total_amount)
    weekly_amount = Decimal(weekly_amount)

    expected_total = (
        weekly_amount * number_of_weeks
    )

    if total_amount != expected_total:
        raise ValidationError(
            {
                "total_amount": (
                    "Total amount must equal "
                    "weekly amount multiplied by "
                    "number of weeks."
                )
            }
        )


def validate_expense_does_not_exceed_budget(
    expense_amount,
    already_spent,
    weekly_budget,
):
    expense_amount = Decimal(expense_amount)
    already_spent = Decimal(already_spent)
    weekly_budget = Decimal(weekly_budget)

    remaining = weekly_budget - already_spent

    if expense_amount > remaining:
        raise ValidationError(
            {
                "amount": (
                    f"Expense exceeds the remaining "
                    f"weekly budget of {remaining} RWF."
                )
            }
        )