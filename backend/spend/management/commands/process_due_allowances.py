from django.core.management.base import BaseCommand

from payments.models import Payout
from payments.payout_services import verify_and_finalize_payout


class Command(BaseCommand):
    help = "Reconcile pending MasterSave allowance payouts."

    def handle(self, *args, **options):
        payouts = Payout.objects.filter(
            kind=Payout.Kind.ALLOWANCE,
            status=Payout.Status.PROCESSING,
            flutterwave_transfer_id__isnull=False,
        )

        reconciled = 0
        for payout in payouts:
            try:
                verify_and_finalize_payout(payout)
                reconciled += 1
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not reconcile payout {payout.id}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciled: {reconciled} allowance payouts."
            )
        )