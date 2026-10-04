import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from allocations.models import DepositAllocation

from .models import (
    InvestmentAccount,
    InvestmentRequest,
    InvestmentTransaction,
)
from .validators import (
    validate_investment_amount,
    validate_request_against_grow_allocation,
)


def generate_reference(prefix):
    return (
        f"MS-{prefix}-"
        f"{uuid.uuid4().hex[:12].upper()}"
    )


def get_reserved_grow_amount(
    allocation,
):
    """
    Amount already committed to investment
    requests from this Grow allocation.
    """

    reserved_statuses = [
        InvestmentRequest.Status.PENDING,
        InvestmentRequest.Status.UNDER_REVIEW,
        InvestmentRequest.Status.APPROVED,
    ]

    return (
        InvestmentRequest.objects
        .filter(
            source_allocation=allocation,
            status__in=reserved_statuses,
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0")
    )


def get_invested_grow_amount(
    allocation,
):
    return (
        InvestmentTransaction.objects
        .filter(
            source_allocation=allocation,
            transaction_type=(
                InvestmentTransaction.TransactionType.CONTRIBUTION
            ),
            status=(
                InvestmentTransaction.Status.CONFIRMED
            ),
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0")
    )


def get_available_grow_amount(
    allocation,
):
    reserved = get_reserved_grow_amount(
        allocation
    )
    invested = get_invested_grow_amount(
        allocation
    )

    return max(
        Decimal("0"),
        allocation.grow_amount
        - reserved
        - invested,
    )


@transaction.atomic
def create_investment_request(
    scholar,
    allocation,
    product,
    amount,
):
    locked_allocation = (
        DepositAllocation.objects
        .select_for_update()
        .get(pk=allocation.pk)
    )

    if (
        locked_allocation.deposit.scholar_id
        != scholar.id
    ):
        raise ValueError(
            "This allocation does not belong to you."
        )

    if (
        locked_allocation.status
        != DepositAllocation.Status.CONFIRMED
    ):
        raise ValueError(
            "This allocation is not available."
        )

    if product.status != product.Status.ACTIVE:
        raise ValueError(
            "This investment product is not active."
        )

    validate_investment_amount(
        amount=amount,
        minimum_amount=product.minimum_amount,
    )

    validate_request_against_grow_allocation(
        amount=amount,
        available_grow_amount=(
            get_available_grow_amount(
                locked_allocation
            )
        ),
    )

    investment_request = (
        InvestmentRequest.objects.create(
            scholar=scholar,
            source_allocation=(
                locked_allocation
            ),
            product=product,
            amount=amount,
            reference=generate_reference(
                "INVEST"
            ),
            status=(
                InvestmentRequest.Status.PENDING
            ),
        )
    )

    return investment_request


@transaction.atomic
def approve_investment_request(
    investment_request,
):
    if investment_request.status not in [
        InvestmentRequest.Status.PENDING,
        InvestmentRequest.Status.UNDER_REVIEW,
    ]:
        raise ValidationError(
            "This investment request cannot be approved."
        )

    investment_request.status = (
        InvestmentRequest.Status.APPROVED
    )
    investment_request.reviewed_at = timezone.now()
    investment_request.save(
        update_fields=[
            "status",
            "reviewed_at",
            "updated_at",
        ]
    )

    return investment_request


@transaction.atomic
def reject_investment_request(
    investment_request,
    reason="",
):
    if investment_request.status not in [
        InvestmentRequest.Status.PENDING,
        InvestmentRequest.Status.UNDER_REVIEW,
    ]:
        raise ValidationError(
            "This investment request cannot be rejected."
        )

    investment_request.status = (
        InvestmentRequest.Status.REJECTED
    )
    investment_request.rejection_reason = reason
    investment_request.reviewed_at = timezone.now()
    investment_request.save(
        update_fields=[
            "status",
            "rejection_reason",
            "reviewed_at",
            "updated_at",
        ]
    )

    return investment_request


@transaction.atomic
def complete_investment_request(
    investment_request,
    partner_account_reference="",
):
    if investment_request.status != (
        InvestmentRequest.Status.APPROVED
    ):
        raise ValidationError(
            "This investment request cannot "
            "be completed."
        )

    now = timezone.now()

    maturity_date = (
        now.date()
        + timedelta(
            days=(
                investment_request
                .product
                .term_months
                * 30
            )
        )
    )

    account = InvestmentAccount.objects.create(
        scholar=investment_request.scholar,
        product=investment_request.product,
        request=investment_request,
        partner_account_reference=(
            partner_account_reference
        ),
        started_at=now,
        maturity_date=maturity_date,
        status=(
            InvestmentAccount.Status.ACTIVE
        ),
    )

    InvestmentTransaction.objects.create(
        account=account,
        source_allocation=(
            investment_request.source_allocation
        ),
        transaction_type=(
            InvestmentTransaction.TransactionType.CONTRIBUTION
        ),
        amount=investment_request.amount,
        reference=generate_reference(
            "INVT"
        ),
        description=(
            "Investment contribution"
        ),
        status=(
            InvestmentTransaction.Status.CONFIRMED
        ),
        occurred_at=now,
    )

    investment_request.status = (
        InvestmentRequest.Status.COMPLETED
    )

    investment_request.completed_at = now
    investment_request.reviewed_at = (
        investment_request.reviewed_at
        or now
    )

    investment_request.save(
        update_fields=[
            "status",
            "completed_at",
            "reviewed_at",
            "updated_at",
        ]
    )

    return account