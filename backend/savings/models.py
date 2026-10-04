import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class SavingsBucket(models.Model):

    class BucketType(models.TextChoices):
        GOAL_LOCK = "GOAL_LOCK", "Goal Lock"
        EMERGENCY = "EMERGENCY", "Emergency Save"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        PAUSED = "PAUSED", "Paused"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    scholar = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="savings_buckets",
    )

    name = models.CharField(
        max_length=100,
    )

    bucket_type = models.CharField(
        max_length=20,
        choices=BucketType.choices,
    )

    target_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("1")),
        ],
    )

    target_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["scholar", "name"],
                name="unique_savings_bucket_name_per_scholar",
            ),
        ]

    @property
    def balance(self):
        contributions = (
            self.transactions
            .filter(
                transaction_type=(
                    SavingsTransaction.TransactionType.CONTRIBUTION
                ),
                status=(
                    SavingsTransaction.Status.CONFIRMED
                ),
            )
            .aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0")
        )

        withdrawals = (
            self.transactions
            .filter(
                transaction_type=(
                    SavingsTransaction.TransactionType.WITHDRAWAL
                ),
                status=(
                    SavingsTransaction.Status.CONFIRMED
                ),
            )
            .aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0")
        )

        return contributions - withdrawals

    @property
    def remaining_to_target(self):
        if not self.target_amount:
            return None

        return max(
            Decimal("0"),
            self.target_amount - self.balance,
        )

    @property
    def progress_percentage(self):
        if not self.target_amount:
            return None

        if self.target_amount == 0:
            return 0

        percentage = (
            self.balance / self.target_amount
        ) * Decimal("100")

        return min(
            Decimal("100"),
            percentage,
        )

    @property
    def is_locked(self):
        return (
            self.bucket_type
            == self.BucketType.GOAL_LOCK
            and (
                not self.target_amount
                or self.balance < self.target_amount
            )
        )

    def __str__(self):
        return (
            f"{self.scholar.email} - "
            f"{self.name}"
        )


class SavingsTransaction(models.Model):

    class TransactionType(models.TextChoices):
        CONTRIBUTION = (
            "CONTRIBUTION",
            "Contribution",
        )
        WITHDRAWAL = (
            "WITHDRAWAL",
            "Withdrawal",
        )

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    bucket = models.ForeignKey(
        SavingsBucket,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    source_allocation = models.ForeignKey(
        "allocations.DepositAllocation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="savings_transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("1")),
        ],
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.reference} - "
            f"{self.amount} RWF"
        )