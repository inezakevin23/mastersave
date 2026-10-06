import uuid

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class AllowancePlan(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
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
        related_name="allowance_plans",
    )

    source_allocation = models.OneToOneField(
        "allocations.DepositAllocation",
        on_delete=models.PROTECT,
        related_name="spend_plan",
    )

    weekly_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(1),
        ],
    )

    number_of_weeks = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(52),
        ],
    )

    start_date = models.DateField()

    release_weekday = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(6),
        ],
        help_text="0 = Monday, 6 = Sunday",
    )

    release_time = models.TimeField(
        default="09:00:00",
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
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["scholar"],
                condition=models.Q(
                    status="ACTIVE"
                ),
                name="one_active_allowance_plan_per_scholar",
            ),
        ]

    @property
    def total_amount(self):
        return self.source_allocation.spend_amount

    def __str__(self):
        return (
            f"{self.scholar.email} - "
            f"{self.total_amount} RWF - "
            f"{self.number_of_weeks} weeks"
        )


class AllowanceRelease(models.Model):

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        PROCESSING = "PROCESSING", "Processing"
        RELEASED = "RELEASED", "Released"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    plan = models.ForeignKey(
        AllowancePlan,
        on_delete=models.PROTECT,
        related_name="releases",
    )

    week_number = models.PositiveSmallIntegerField()

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[
            MinValueValidator(1),
        ],
    )

    scheduled_at = models.DateTimeField()

    released_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    provider = models.CharField(
        max_length=50,
        blank=True,
    )

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
    )

    failure_reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["week_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["plan", "week_number"],
                name="unique_plan_week_release",
            ),
        ]

    def __str__(self):
        return (
            f"{self.plan.scholar.email} - "
            f"Week {self.week_number}"
        )


