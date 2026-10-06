from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from allocations.models import DepositAllocation
from deposits.models import Deposit
from spend.models import AllowancePlan, AllowanceRelease
from savings.models import (
    SavingsBucket,
    SavingsTransaction,
)
from investments.summary import get_grow_summary


def get_spend_summary(scholar):
    plan = (
        AllowancePlan.objects
        .filter(
            scholar=scholar,
            status=AllowancePlan.Status.ACTIVE,
        )
        .prefetch_related("releases")
        .first()
    )

    if plan is None:
        return {
            "allocated": 0,
            "current_week": None,
            "total_weeks": None,
            "weekly_amount": None,
            "current_release": None,
            "next_release": None,
            "withdrawal_release": None,
        }

    now = timezone.now()

    current_release = (
        plan.releases
        .filter(
            scheduled_at__lte=now,
            status__in=[
                AllowanceRelease.Status.PROCESSING,
                AllowanceRelease.Status.RELEASED,
                AllowanceRelease.Status.FAILED,
            ],
        )
        .order_by("-week_number")
        .first()
    )

    next_release = (
        plan.releases
        .filter(
            scheduled_at__gt=now,
            status=AllowanceRelease.Status.SCHEDULED,
        )
        .order_by("scheduled_at")
        .first()
    )

    withdrawal_release = (
        plan.releases
        .filter(
            scheduled_at__lte=now,
            status=AllowanceRelease.Status.SCHEDULED,
        )
        .order_by("scheduled_at")
        .first()
    )

    return {
        "allocated": plan.total_amount,
        "current_week": (
            current_release.week_number
            if current_release
            else None
        ),
        "total_weeks": plan.number_of_weeks,
        "weekly_amount": plan.weekly_amount,
        "current_release": (
            {
                "id": str(current_release.id),
                "amount": current_release.amount,
                "status": current_release.status,
                "released_at": current_release.released_at,
            }
            if current_release
            else None
        ),
        "next_release": (
            {
                "id": str(next_release.id),
                "amount": next_release.amount,
                "scheduled_at": next_release.scheduled_at,
            }
            if next_release
            else None
        ),
        "withdrawal_release": (
            {
                "id": str(withdrawal_release.id),
                "week_number": withdrawal_release.week_number,
                "amount": withdrawal_release.amount,
                "scheduled_at": withdrawal_release.scheduled_at,
            }
            if withdrawal_release
            else None
        ),
    }


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scholar = request.user

        deposits = Deposit.objects.filter(
            scholar=scholar,
            status=Deposit.Status.SUCCESSFUL,
        )

        total_deposited = (
            deposits.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        allocations = (
            DepositAllocation.objects
            .filter(
                deposit__scholar=scholar,
                deposit__status=Deposit.Status.SUCCESSFUL,
                status=DepositAllocation.Status.CONFIRMED,
            )
            .aggregate(
                spend=Sum("spend_amount"),
                save=Sum("save_amount"),
                grow=Sum("grow_amount"),
            )
        )

        spend_allocated = (
            allocations["spend"]
            or Decimal("0")
        )

        save_allocated = (
            allocations["save"]
            or Decimal("0")
        )

        grow_allocated = (
            allocations["grow"]
            or Decimal("0")
        )

        total_allocated = (
            spend_allocated
            + save_allocated
            + grow_allocated
        )

        unallocated = (
            total_deposited
            - total_allocated
        )

        savings_buckets = (
            SavingsBucket.objects
            .filter(
                scholar=scholar,
                status__in=[
                    SavingsBucket.Status.ACTIVE,
                    SavingsBucket.Status.COMPLETED,
                ],
            )
            .prefetch_related("transactions")
        )

        total_saved = Decimal("0")

        savings_data = []

        for bucket in savings_buckets:
            balance = bucket.balance

            total_saved += balance

            savings_data.append(
                {
                    "id": str(bucket.id),
                    "name": bucket.name,
                    "type": bucket.bucket_type,
                    "balance": balance,
                    "target_amount": (
                        bucket.target_amount
                    ),
                    "remaining_to_target": (
                        bucket.remaining_to_target
                    ),
                    "progress_percentage": (
                        bucket.progress_percentage
                    ),
                    "is_locked": (
                        bucket.is_locked
                    ),
                    "status": bucket.status,
                }
            )

        grow_summary = get_grow_summary(
            scholar
        )

        spend_data = get_spend_summary(scholar)

        return Response(
            {
                "success": True,
                "data": {
                    "total_deposited":
                        total_deposited,

                    "total_allocated":
                        total_allocated,

                    "unallocated":
                        unallocated,

                    "currency": "RWF",

                    "spend": spend_data,

                    "save": {
                        "allocated":
                            save_allocated,
                        "total_saved": total_saved,
                        "unassigned": max(
                            Decimal("0"),
                            save_allocated - total_saved,
                        ),
                        "buckets": savings_data,
                        "implemented": True,
                    },

                    "grow": {
                        "allocated": grow_summary[
                            "allocated"
                        ],
                        "reserved": grow_summary[
                            "reserved"
                        ],
                        "invested": grow_summary[
                            "invested"
                        ],
                        "available": grow_summary[
                            "available"
                        ],
                        "investment_balance": (
                            grow_summary[
                                "investment_balance"
                            ]
                        ),
                        "projected_return": (
                            grow_summary[
                                "projected_return"
                            ]
                        ),
                        "accounts": grow_summary[
                            "accounts"
                        ],
                        "implemented": True,
                    },
                },
            }
        )