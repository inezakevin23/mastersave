import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Deposit(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESSFUL = "SUCCESSFUL", "Successful"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    class Source(models.TextChoices):
        ALLOWANCE = "ALLOWANCE", "Allowance"
        FLUTTERWAVE = "FLUTTERWAVE", "Flutterwave"
        MANUAL = "MANUAL", "Manual"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    scholar = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="deposits",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(1),
        ],
    )

    currency = models.CharField(
        max_length=3,
        default="RWF",
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
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

    description = models.CharField(
        max_length=255,
        blank=True,
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
        return f"{self.reference} - {self.amount} {self.currency}"