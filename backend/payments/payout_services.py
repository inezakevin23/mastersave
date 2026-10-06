import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from savings.models import SavingsBucket
from savings.services import create_withdrawal
from spend.models import AllowanceRelease

from .flutterwave import (
    FlutterwaveClient,
    FlutterwaveError,
    FlutterwaveTransportError,
)
from .models import Payout, PayoutDestination
from .validators import validate_rwf_amount, validate_verified_transfer


def generate_payout_reference():
    return f"MS-PAYOUT-{uuid.uuid4().hex[:16].upper()}"


def get_pending_savings_withdrawals(bucket):
    return (
        Payout.objects
        .filter(
            savings_bucket=bucket,
            kind=Payout.Kind.SAVINGS_WITHDRAWAL,
            status__in=[
                Payout.Status.REQUESTED,
                Payout.Status.PROCESSING,
            ],
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )


@transaction.atomic
def create_savings_withdrawal_payout(
    *,
    scholar,
    bucket,
    amount,
    destination,
):
    amount = Decimal(str(amount))
    validate_rwf_amount(amount)

    bucket = SavingsBucket.objects.select_for_update().get(pk=bucket.pk)

    if bucket.scholar_id != scholar.id:
        raise ValidationError(
            {"bucket": "This savings bucket does not belong to you."}
        )

    if destination.scholar_id != scholar.id:
        raise ValidationError(
            {"destination": "This payout destination does not belong to you."}
        )

    if (
        bucket.bucket_type == SavingsBucket.BucketType.GOAL_LOCK
        and bucket.is_locked
    ):
        raise ValidationError({"bucket": "Goal Lock is still locked."})

    available = (
        bucket.balance - get_pending_savings_withdrawals(bucket)
    )
    if amount > available:
        raise ValidationError(
            {
                "amount": (
                    f"Only {available} RWF is currently available "
                    "for withdrawal."
                )
            }
        )

    return Payout.objects.create(
        scholar=scholar,
        kind=Payout.Kind.SAVINGS_WITHDRAWAL,
        amount=amount,
        currency="RWF",
        reference=generate_payout_reference(),
        destination=destination,
        savings_bucket=bucket,
        status=Payout.Status.REQUESTED,
    )


@transaction.atomic
def create_allowance_payout(*, release, destination):
    release = (
        AllowanceRelease.objects
        .select_for_update()
        .select_related("plan", "plan__scholar")
        .get(pk=release.pk)
    )

    existing_payout = Payout.objects.filter(
        allowance_release=release
    ).first()
    if existing_payout:
        if existing_payout.status in [
            Payout.Status.REQUESTED,
            Payout.Status.PROCESSING,
            Payout.Status.SUCCESSFUL,
        ]:
            return existing_payout
        raise ValidationError(
            {"release": "A payout already exists for this release."}
        )

    if release.status != AllowanceRelease.Status.SCHEDULED:
        raise ValidationError(
            {"release": "This allowance release is not scheduled."}
        )

    now = timezone.now()
    if release.scheduled_at > now:
        raise ValidationError(
            {"release": "This allowance release is not due yet."}
        )

    if destination.scholar_id != release.plan.scholar_id:
        raise ValidationError(
            {"destination": "Destination does not belong to the scholar."}
        )

    payout = Payout.objects.create(
        scholar=release.plan.scholar,
        kind=Payout.Kind.ALLOWANCE,
        amount=release.amount,
        currency="RWF",
        reference=generate_payout_reference(),
        destination=destination,
        allowance_release=release,
        status=Payout.Status.REQUESTED,
    )

    release.status = AllowanceRelease.Status.PROCESSING
    release.save(update_fields=["status", "updated_at"])
    return payout


def send_payout_to_flutterwave(payout):
    error = None
    result = None

    with transaction.atomic():
        locked_payout = (
            Payout.objects
            .select_for_update()
            .select_related("destination")
            .get(pk=payout.pk)
        )

        if locked_payout.flutterwave_transfer_id:
            return locked_payout

        if locked_payout.status not in [
            Payout.Status.REQUESTED,
            Payout.Status.PROCESSING,
        ]:
            raise ValidationError(
                "Only requested or processing payouts can be sent."
            )

        if locked_payout.provider_status == "SUBMISSION_UNKNOWN":
            raise ValidationError(
                "Transfer outcome is unknown; reconcile with Flutterwave "
                "before retrying to avoid a duplicate payout."
            )

        try:
            response = FlutterwaveClient().create_transfer(
                destination=locked_payout.destination,
                amount=locked_payout.amount,
                reference=locked_payout.reference,
                narration=f"MasterSave {locked_payout.get_kind_display()}",
            )
            data = response.get("data")
            if not isinstance(data, dict) or data.get("id") is None:
                raise FlutterwaveError(
                    "Flutterwave returned no transfer ID."
                )

            locked_payout.flutterwave_transfer_id = int(data["id"])
            locked_payout.provider_reference = str(
                data.get("reference", "")
            )
            locked_payout.provider_status = str(data.get("status", ""))
            locked_payout.raw_response = response
            locked_payout.status = Payout.Status.PROCESSING
            locked_payout.initiated_at = (
                locked_payout.initiated_at or timezone.now()
            )
            locked_payout.save(
                update_fields=[
                    "flutterwave_transfer_id",
                    "provider_reference",
                    "provider_status",
                    "raw_response",
                    "status",
                    "initiated_at",
                    "updated_at",
                ]
            )
            result = locked_payout
        except FlutterwaveTransportError as exc:
            locked_payout.status = Payout.Status.PROCESSING
            locked_payout.provider_status = "SUBMISSION_UNKNOWN"
            locked_payout.raw_response = {"submission_error": str(exc)}
            locked_payout.save(
                update_fields=[
                    "status",
                    "provider_status",
                    "raw_response",
                    "updated_at",
                ]
            )
            error = exc
        except Exception as exc:
            locked_payout.status = Payout.Status.FAILED
            locked_payout.provider_status = "FAILED"
            locked_payout.failure_reason = str(exc)
            locked_payout.raw_response = {"error": str(exc)}
            locked_payout.save(
                update_fields=[
                    "status",
                    "provider_status",
                    "failure_reason",
                    "raw_response",
                    "updated_at",
                ]
            )
            error = exc

    if error:
        raise error
    return result


@transaction.atomic
def mark_payout_successful(*, payout, verified_data):
    payout = (
        Payout.objects
        .select_for_update(of=("self",))
        .select_related(
            "scholar",
            "allowance_release",
            "savings_bucket",
            "investment_account",
        )
        .get(pk=payout.pk)
    )

    if payout.status == Payout.Status.SUCCESSFUL:
        return payout

    if payout.kind == Payout.Kind.INVESTMENT_WITHDRAWAL:
        raise ValidationError(
            "Investment withdrawal finalization is not implemented."
        )

    validate_verified_transfer(
        payout=payout,
        verified_data=verified_data,
    )

    now = timezone.now()
    payout.status = Payout.Status.SUCCESSFUL
    payout.provider_status = str(verified_data.get("status", ""))
    payout.provider_reference = str(
        verified_data.get("reference", payout.provider_reference)
    )
    payout.fee = verified_data.get("fee")
    payout.completed_at = now
    payout.raw_response = verified_data
    payout.save(
        update_fields=[
            "status",
            "provider_status",
            "provider_reference",
            "fee",
            "completed_at",
            "raw_response",
            "updated_at",
        ]
    )

    if payout.kind == Payout.Kind.ALLOWANCE:
        release = payout.allowance_release
        release.status = AllowanceRelease.Status.RELEASED
        release.released_at = now
        release.provider = "flutterwave"
        release.provider_reference = payout.provider_reference
        release.failure_reason = ""
        release.save(
            update_fields=[
                "status",
                "released_at",
                "provider",
                "provider_reference",
                "failure_reason",
                "updated_at",
            ]
        )
    elif payout.kind == Payout.Kind.SAVINGS_WITHDRAWAL:
        if payout.savings_transaction_id is None:
            bucket = SavingsBucket.objects.select_for_update().get(
                pk=payout.savings_bucket_id
            )
            other_pending = get_pending_savings_withdrawals(bucket)
            if payout.amount > bucket.balance - other_pending:
                raise ValidationError(
                    "The savings balance changed before payout completion."
                )

            payout.savings_transaction = create_withdrawal(
                bucket,
                payout.amount,
                description="Savings withdrawal payout",
            )
            payout.save(
                update_fields=["savings_transaction", "updated_at"]
            )

    return payout


@transaction.atomic
def mark_payout_failed(*, payout, reason):
    payout = Payout.objects.select_for_update().get(pk=payout.pk)

    if payout.status == Payout.Status.SUCCESSFUL:
        raise ValidationError(
            "A successful payout cannot be marked failed."
        )
    if payout.status == Payout.Status.FAILED:
        return payout

    payout.status = Payout.Status.FAILED
    payout.failure_reason = reason
    payout.provider_status = "FAILED"
    payout.save(
        update_fields=[
            "status",
            "failure_reason",
            "provider_status",
            "updated_at",
        ]
    )

    if payout.allowance_release_id:
        release = AllowanceRelease.objects.select_for_update().get(
            pk=payout.allowance_release_id
        )
        if release.status == AllowanceRelease.Status.RELEASED:
            raise ValidationError(
                "A released allowance cannot be marked failed."
            )
        release.status = AllowanceRelease.Status.FAILED
        release.failure_reason = reason
        release.save(
            update_fields=["status", "failure_reason", "updated_at"]
        )

    return payout


def verify_and_finalize_payout(payout):
    if not payout.flutterwave_transfer_id:
        raise ValidationError(
            "Payout has no Flutterwave transfer ID."
        )

    response = FlutterwaveClient().verify_transfer(
        payout.flutterwave_transfer_id
    )
    verified_data = response.get("data")
    if not isinstance(verified_data, dict):
        raise ValidationError(
            "Flutterwave verification returned no transfer data."
        )

    status = str(verified_data.get("status", "")).upper()
    if status == "SUCCESSFUL":
        return mark_payout_successful(
            payout=payout,
            verified_data=verified_data,
        )

    if status in {"FAILED", "REVERSED", "CANCELLED"}:
        reason = (
            verified_data.get("complete_message")
            or verified_data.get("status")
            or "Transfer failed."
        )
        return mark_payout_failed(payout=payout, reason=str(reason))

    return payout
