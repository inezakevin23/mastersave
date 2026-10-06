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
    plans = list(
        AllowancePlan.objects
        .filter(
            scholar=scholar,
            status=AllowancePlan.Status.ACTIVE,
        )
        .select_related("source_allocation")
        .prefetch_related("releases")
    )

    if not plans:
        return {
            "allocated": 0,
            "current_week": None,
            "total_weeks": None,
            "weekly_amount": None,
            "current_release": None,
            "next_release": None,
            "withdrawal_release": None,
            "withdrawal_releases": [],
            "plans": [],
        }

    today = timezone.localdate()

    plan_data = []
    current_releases = []
    next_releases = []
    withdrawal_releases = []

    for plan in plans:
        current_release = (
            plan.releases
            .filter(
                scheduled_at__date__lte=today,
            )
            .order_by("-scheduled_at", "-week_number")
            .first()
        )
        next_release = (
            plan.releases
            .filter(
                scheduled_at__date__gt=today,
                status=AllowanceRelease.Status.SCHEDULED,
            )
            .order_by("scheduled_at")
            .first()
        )
        due_releases = (
            [current_release]
            if current_release
            and current_release.status == AllowanceRelease.Status.SCHEDULED
            else []
        )

        if current_release:
            current_releases.append(current_release)
        if next_release:
            next_releases.append(next_release)
        withdrawal_releases.extend(due_releases)

        plan_data.append(
            {
                "id": str(plan.id),
                "allocated": plan.total_amount,
                "weekly_amount": plan.weekly_amount,
                "number_of_weeks": plan.number_of_weeks,
                "start_date": plan.start_date,
                "current_week": (
                    current_release.week_number
                    if current_release
                    else None
                ),
            }
        )

    current_release = max(
        current_releases,
        key=lambda release: release.scheduled_at,
        default=None,
    )
    next_release = min(
        next_releases,
        key=lambda release: release.scheduled_at,
        default=None,
    )
    withdrawal_releases.sort(key=lambda release: release.scheduled_at)
    withdrawal_release = (
        withdrawal_releases[0]
        if withdrawal_releases
        else None
    )
    current_plan = next(
        (
            plan
            for plan in plans
            if current_release
            and plan.id == current_release.plan_id
        ),
        plans[0],
    )

    def release_data(release):
        if release is None:
            return None
        return {
            "id": str(release.id),
            "plan_id": str(release.plan_id),
            "week_number": release.week_number,
            "amount": release.amount,
            "status": release.status,
            "scheduled_at": release.scheduled_at,
            "released_at": release.released_at,
        }

    return {
        "allocated": sum(
            (plan.total_amount for plan in plans),
            Decimal("0"),
        ),
        "current_week": (
            current_release.week_number
            if current_release
            else None
        ),
        "total_weeks": current_plan.number_of_weeks,
        "weekly_amount": sum(
            (plan.weekly_amount for plan in plans),
            Decimal("0"),
        ),
        "current_release": release_data(current_release),
        "next_release": release_data(next_release),
        "withdrawal_release": release_data(withdrawal_release),
        "withdrawal_releases": [
            release_data(release)
            for release in withdrawal_releases
        ],
        "plans": plan_data,
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
                        "allocations": grow_summary[
                            "allocations"
                        ],
                        "accounts": grow_summary[
                            "accounts"
                        ],
                        "implemented": True,
                    },
                },
            }
        )
