from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Deposit


@transaction.atomic
def create_successful_deposit(
    *,
    scholar,
    amount,
    source,
    reference,
    description="",
    currency="RWF",
):
    deposit = (
        Deposit.objects
        .select_for_update()
        .filter(reference=reference)
        .first()
    )

    if deposit is None:
        return Deposit.objects.create(
            scholar=scholar,
            amount=amount,
            currency=currency,
            source=source,
            status=Deposit.Status.SUCCESSFUL,
            reference=reference,
            description=description,
            confirmed_at=timezone.now(),
        )

    if (
        deposit.scholar_id != scholar.id
        or deposit.amount != amount
        or deposit.currency != currency
        or deposit.source != source
    ):
        raise ValidationError(
            "An existing deposit does not match the verified payment."
        )

    if deposit.status == Deposit.Status.REVERSED:
        raise ValidationError(
            "A reversed deposit cannot be confirmed again."
        )

    deposit.status = Deposit.Status.SUCCESSFUL
    deposit.description = description or deposit.description
    deposit.confirmed_at = deposit.confirmed_at or timezone.now()
    deposit.save(
        update_fields=[
            "status",
            "description",
            "confirmed_at",
            "updated_at",
        ]
    )
    return deposit