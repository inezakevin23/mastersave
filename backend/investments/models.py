import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class InvestmentProduct(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=150,
    )

    partner_name = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    currency = models.CharField(
        max_length=3,
        default="RWF",
    )

    minimum_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("1")),
        ],
    )

    annual_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0")),
        ],
        help_text="Indicative annual rate in percent.",
    )

    term_months = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
    )

    risk_information = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def projected_return(self, principal):
        """
        Simple annual-rate projection.

        This is an estimate for display only.
        It is not a guarantee of actual investment returns.
        """
        principal = Decimal(principal)

        return (
            principal
            * (self.annual_rate / Decimal("100"))
            * (
                Decimal(self.term_months)
                / Decimal("12")
            )
        )

    def __str__(self):
        return self.name


class InvestmentRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        UNDER_REVIEW = (
            "UNDER_REVIEW",
            "Under Review",
        )
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    scholar = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investment_requests",
    )

    source_allocation = models.ForeignKey(
        "allocations.DepositAllocation",
        on_delete=models.PROTECT,
        related_name="investment_requests",
    )

    product = models.ForeignKey(
        InvestmentProduct,
        on_delete=models.PROTECT,
        related_name="investment_requests",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("1")),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
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
        ordering = ["-requested_at"]

    def __str__(self):
        return (
            f"{self.reference} - "
            f"{self.amount} RWF"
        )


class InvestmentAccount(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        MATURED = "MATURED", "Matured"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    scholar = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investment_accounts",
    )

    product = models.ForeignKey(
        InvestmentProduct,
        on_delete=models.PROTECT,
        related_name="investment_accounts",
    )

    request = models.OneToOneField(
        InvestmentRequest,
        on_delete=models.PROTECT,
        related_name="investment_account",
    )

    partner_account_reference = models.CharField(
        max_length=255,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    maturity_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    @property
    def balance(self):
        contributions = (
            self.transactions
            .filter(
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

        returns = (
            self.transactions
            .filter(
                transaction_type=(
                    InvestmentTransaction.TransactionType.RETURN
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

        withdrawals = (
            self.transactions
            .filter(
                transaction_type=(
                    InvestmentTransaction.TransactionType.WITHDRAWAL
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

        fees = (
            self.transactions
            .filter(
                transaction_type=(
                    InvestmentTransaction.TransactionType.FEE
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

        return (
            contributions
            + returns
            - withdrawals
            - fees
        )

    @property
    def principal(self):
        return (
            self.transactions
            .filter(
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

    @property
    def projected_return(self):
        return self.product.projected_return(
            self.principal
        )

    def __str__(self):
        return (
            f"{self.scholar.email} - "
            f"{self.product.name}"
        )


class InvestmentTransaction(models.Model):

    class TransactionType(models.TextChoices):
        CONTRIBUTION = (
            "CONTRIBUTION",
            "Contribution",
        )
        RETURN = (
            "RETURN",
            "Return",
        )
        WITHDRAWAL = (
            "WITHDRAWAL",
            "Withdrawal",
        )
        FEE = (
            "FEE",
            "Fee",
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

    account = models.ForeignKey(
        InvestmentAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    source_allocation = models.ForeignKey(
        "allocations.DepositAllocation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="investment_transactions",
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

    occurred_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return (
            f"{self.reference} - "
            f"{self.amount} RWF"
        )