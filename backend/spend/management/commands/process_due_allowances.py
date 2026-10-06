from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import Payout, PayoutDestination
from payments.payout_services import (
    create_allowance_payout,
    send_payout_to_flutterwave,
    verify_and_finalize_payout,
)
from spend.models import AllowancePlan, AllowanceRelease


class Command(BaseCommand):
    help = "Process due MasterSave allowance releases."

    def handle(self, *args, **options):
        now = timezone.now()
        processing_payouts = Payout.objects.filter(
            status=Payout.Status.PROCESSING,
            flutterwave_transfer_id__isnull=False,
        )
        for payout in processing_payouts:
            try:
                verify_and_finalize_payout(payout)
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not reconcile payout {payout.id}: {exc}"
                    )
                )

        releases = (
            AllowanceRelease.objects
            .filter(
                plan__status=AllowancePlan.Status.ACTIVE,
                status=AllowanceRelease.Status.SCHEDULED,
                scheduled_at__lte=now,
            )
            .select_related("plan", "plan__scholar")
            .order_by("scheduled_at")
        )

        processed = 0
        skipped = 0

        for release in releases:
            scholar = release.plan.scholar
            destination = PayoutDestination.objects.filter(
                scholar=scholar,
                is_default=True,
            ).first()

            if destination is None:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping week {release.week_number} for "
                        f"{scholar.email}: no default payout destination."
                    )
                )
                continue

            try:
                payout = create_allowance_payout(
                    release=release,
                    destination=destination,
                )
                send_payout_to_flutterwave(payout)
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed release {release.id}."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed release {release.id}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed: {processed}; Skipped: {skipped}"
            )
        )