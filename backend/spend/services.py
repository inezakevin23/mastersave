from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import AllowancePlan, AllowanceRelease


def build_release_datetime(
    start_date,
    release_time,
    week_number,
):
    naive_datetime = datetime.combine(
        start_date + timedelta(
            weeks=week_number - 1
        ),
        release_time,
    )

    return timezone.make_aware(
        naive_datetime,
        timezone.get_current_timezone(),
    )


@transaction.atomic
def create_allowance_releases(plan):
    releases = []

    for week_number in range(
        1,
        plan.number_of_weeks + 1,
    ):
        scheduled_at = build_release_datetime(
            plan.start_date,
            plan.release_time,
            week_number,
        )

        releases.append(
            AllowanceRelease(
                plan=plan,
                week_number=week_number,
                amount=plan.weekly_amount,
                scheduled_at=scheduled_at,
            )
        )

    AllowanceRelease.objects.bulk_create(
        releases
    )

    return releases


@transaction.atomic
def sync_releases(plan):
    now = timezone.now()

    releases = plan.releases.filter(
        status=AllowanceRelease.Status.SCHEDULED,
        scheduled_at__lte=now,
    )

    releases.update(
        status=AllowanceRelease.Status.RELEASED,
        released_at=now,
    )