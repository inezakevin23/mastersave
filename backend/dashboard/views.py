from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from deposits.models import Deposit
from spend.models import AllowancePlan
from spend.services import sync_releases


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scholar = request.user

        total_deposited = (
            Deposit.objects
            .filter(
                scholar=scholar,
                status=Deposit.Status.SUCCESSFUL,
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        plan = (
            AllowancePlan.objects
            .filter(
                scholar=scholar,
                status=AllowancePlan.Status.ACTIVE,
            )
            .prefetch_related(
                "releases",
                "releases__expenses",
            )
            .first()
        )

        spend_data = {
            "allocated": Decimal("0"),
            "current_week": None,
            "total_weeks": None,
            "weekly_budget": None,
            "used_this_week": None,
            "remaining_this_week": None,
            "next_release": None,
        }

        if plan:
            sync_releases(plan)

            releases = list(
                plan.releases.order_by(
                    "week_number"
                )
            )

            now = timezone.now()

            current_release = None

            for release in releases:
                next_release = next(
                    (
                        r
                        for r in releases
                        if r.week_number
                        == release.week_number + 1
                    ),
                    None,
                )

                if (
                    release.status
                    == release.Status.RELEASED
                    and release.scheduled_at <= now
                    and (
                        next_release is None
                        or next_release.scheduled_at > now
                    )
                ):
                    current_release = release
                    break

            if current_release:
                used = (
                    current_release.expenses
                    .aggregate(
                        total=Sum("amount")
                    )["total"]
                    or Decimal("0")
                )

                remaining = max(
                    Decimal("0"),
                    current_release.amount - used,
                )

                spend_data = {
                    "allocated": plan.total_amount,
                    "current_week": (
                        current_release.week_number
                    ),
                    "total_weeks": (
                        plan.number_of_weeks
                    ),
                    "weekly_budget": (
                        current_release.amount
                    ),
                    "used_this_week": used,
                    "remaining_this_week": remaining,
                    "next_release": next(
                        (
                            r.scheduled_at
                            for r in releases
                            if r.status
                            == r.Status.SCHEDULED
                        ),
                        None,
                    ),
                }

        return Response(
            {
                "success": True,
                "data": {
                    "total_deposited":
                        total_deposited,

                    "currency": "RWF",

                    "spend": spend_data,

                    "save": {
                        "allocated": None,
                        "implemented": False,
                    },

                    "grow": {
                        "allocated": None,
                        "implemented": False,
                    },
                },
            }
        )