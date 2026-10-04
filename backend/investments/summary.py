from decimal import Decimal

from django.db.models import Sum

from allocations.models import DepositAllocation

from .models import (
    InvestmentAccount,
)
from .services import (
    get_available_grow_amount,
    get_invested_grow_amount,
    get_reserved_grow_amount,
)


def get_grow_summary(scholar):
    allocations = (
        DepositAllocation.objects
        .filter(
            deposit__scholar=scholar,
            deposit__status="SUCCESSFUL",
            status=(
                DepositAllocation.Status.CONFIRMED
            ),
        )
    )

    total_allocated = (
        allocations.aggregate(
            total=Sum("grow_amount")
        )["total"]
        or Decimal("0")
    )

    total_reserved = Decimal("0")
    total_invested = Decimal("0")

    allocation_data = []

    for allocation in allocations:
        reserved = get_reserved_grow_amount(
            allocation
        )

        invested = get_invested_grow_amount(
            allocation
        )

        available = get_available_grow_amount(
            allocation
        )

        total_reserved += reserved
        total_invested += invested

        allocation_data.append(
            {
                "allocation_id": str(
                    allocation.id
                ),
                "allocated": allocation.grow_amount,
                "reserved": reserved,
                "invested": invested,
                "available": available,
            }
        )

    total_available = max(
        Decimal("0"),
        total_allocated
        - total_reserved
        - total_invested,
    )

    accounts = (
        InvestmentAccount.objects
        .filter(
            scholar=scholar,
            status__in=[
                InvestmentAccount.Status.ACTIVE,
                InvestmentAccount.Status.MATURED,
            ],
        )
        .select_related("product")
        .prefetch_related("transactions")
    )

    total_balance = Decimal("0")
    total_projected_return = Decimal("0")

    account_data = []

    for account in accounts:
        balance = account.balance
        projected_return = (
            account.projected_return
        )

        total_balance += balance
        total_projected_return += (
            projected_return
        )

        account_data.append(
            {
                "id": str(account.id),
                "product_name": (
                    account.product.name
                ),
                "partner_name": (
                    account.product.partner_name
                ),
                "principal": account.principal,
                "balance": balance,
                "annual_rate": (
                    account.product.annual_rate
                ),
                "term_months": (
                    account.product.term_months
                ),
                "projected_return": (
                    projected_return
                ),
                "status": account.status,
                "maturity_date": (
                    account.maturity_date
                ),
            }
        )

    return {
        "allocated": total_allocated,
        "reserved": total_reserved,
        "invested": total_invested,
        "available": total_available,
        "investment_balance": total_balance,
        "projected_return": (
            total_projected_return
        ),
        "allocations": allocation_data,
        "accounts": account_data,
    }