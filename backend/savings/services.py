import uuid

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from allocations.models import DepositAllocation

from .models import (
    SavingsBucket,
    SavingsTransaction,
)
from .validators import (
    validate_bucket_withdrawal,
    validate_contribution_amount,
    validate_withdrawal_amount,
)


def generate_reference(prefix):
    return (
        f"MS-{prefix}-"
        f"{uuid.uuid4().hex[:12].upper()}"
    )


def get_bucket_balance(bucket):
    contributions = (
        bucket.transactions
        .filter(
            transaction_type=(
                SavingsTransaction.TransactionType.CONTRIBUTION
            ),
            status=(
                SavingsTransaction.Status.CONFIRMED
            ),
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    withdrawals = (
        bucket.transactions
        .filter(
            transaction_type=(
                SavingsTransaction.TransactionType.WITHDRAWAL
            ),
            status=(
                SavingsTransaction.Status.CONFIRMED
            ),
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    return contributions - withdrawals


@transaction.atomic
def create_contribution(
    bucket,
    allocation,
    amount,
    description="",
):
    locked_allocation = (
        DepositAllocation.objects
        .select_for_update()
        .get(pk=allocation.pk)
    )

    confirmed_contributions = (
        SavingsTransaction.objects
        .filter(
            source_allocation=locked_allocation,
            transaction_type=(
                SavingsTransaction.TransactionType.CONTRIBUTION
            ),
            status=(
                SavingsTransaction.Status.CONFIRMED
            ),
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    remaining_allocation = (
        locked_allocation.save_amount
        - confirmed_contributions
    )

    validate_contribution_amount(
        amount=amount,
        remaining_allocation=remaining_allocation,
    )

    transaction_record = (
        SavingsTransaction.objects.create(
            bucket=bucket,
            source_allocation=locked_allocation,
            transaction_type=(
                SavingsTransaction.TransactionType.CONTRIBUTION
            ),
            amount=amount,
            reference=generate_reference("SAVE"),
            description=description,
            status=(
                SavingsTransaction.Status.CONFIRMED
            ),
            confirmed_at=timezone.now(),
        )
    )

    update_bucket_status(bucket)

    return transaction_record


@transaction.atomic
def create_withdrawal(
    bucket,
    amount,
    description="",
):
    balance = get_bucket_balance(bucket)

    validate_bucket_withdrawal(
        bucket_type=bucket.bucket_type,
        balance=balance,
        target_amount=bucket.target_amount,
    )

    validate_withdrawal_amount(
        amount=amount,
        available_balance=balance,
    )

    transaction_record = (
        SavingsTransaction.objects.create(
            bucket=bucket,
            transaction_type=(
                SavingsTransaction.TransactionType.WITHDRAWAL
            ),
            amount=amount,
            reference=generate_reference("WITHDRAW"),
            description=description,
            status=(
                SavingsTransaction.Status.CONFIRMED
            ),
            confirmed_at=timezone.now(),
        )
    )

    update_bucket_status(bucket)

    return transaction_record


def update_bucket_status(bucket):
    balance = get_bucket_balance(bucket)

    if (
        bucket.bucket_type
        == SavingsBucket.BucketType.GOAL_LOCK
        and bucket.target_amount
        and balance >= bucket.target_amount
    ):
        bucket.status = (
            SavingsBucket.Status.COMPLETED
        )
        bucket.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )