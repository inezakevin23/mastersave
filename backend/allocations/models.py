import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class DepositAllocation(models.Model):

    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        LOCKED = "LOCKED", "Locked"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    deposit = models.OneToOneField(
        "deposits.Deposit",
        on_delete=models.PROTECT,
        related_name="allocation",
    )

    spend_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("0")),
        ],
    )

    save_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("0")),
        ],
    )

    grow_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(Decimal("0")),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
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
    def total_allocated(self):
        return (
            self.spend_amount
            + self.save_amount
            + self.grow_amount
        )

    def clean(self):
        super().clean()

        if not self.deposit_id:
            return

        if self.deposit.status != (
            self.deposit.Status.SUCCESSFUL
        ):
            raise ValidationError(
                {
                    "deposit": (
                        "Only successful deposits "
                        "can be allocated."
                    )
                }
            )

        deposit_amount = self.deposit.amount

        if self.total_allocated != deposit_amount:
            raise ValidationError(
                {
                    "spend_amount": (
                        "Spend, Save and Grow must "
                        "add up exactly to the deposit amount."
                    )
                }
            )

        if (
            self.spend_amount < 0
            or self.save_amount < 0
            or self.grow_amount < 0
        ):
            raise ValidationError(
                "Allocation amounts cannot be negative."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.deposit.scholar.email} - "
            f"{self.deposit.reference}"
        )