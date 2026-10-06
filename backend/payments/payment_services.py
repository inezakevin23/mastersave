import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from deposits.models import Deposit
from deposits.services import create_successful_deposit

from .flutterwave import (
    FlutterwaveClient,
    FlutterwaveTransportError,
)
from .models import Payment
from .validators import (
    validate_rwf_amount,
    validate_verified_charge,
)


def generate_reference(prefix):
    return f"MS-{prefix}-{uuid.uuid4().hex[:16].upper()}"


def initiate_mobile_money_deposit(*, scholar, amount):
    validate_rwf_amount(amount)

    payment = Payment.objects.create(
        scholar=scholar,
        reference=generate_reference("PAY"),
        order_id=generate_reference("ORDER"),
        amount=amount,
        currency="RWF",
        payment_method="mobilemoneyrw",
        status=Payment.Status.PENDING,
    )

    try:
        response = FlutterwaveClient().charge_rwanda_mobile_money(
            amount=amount,
            email=scholar.email,
            phone_number=scholar.phone,
            fullname=f"{scholar.first_name} {scholar.last_name}".strip(),
            tx_ref=payment.reference,
            order_id=payment.order_id,
        )
    except FlutterwaveTransportError as exc:
        payment.status = Payment.Status.PROCESSING
        payment.raw_response = {"error": str(exc)}
        payment.save(
            update_fields=["status", "raw_response", "updated_at"]
        )
        return payment
    except Exception as exc:
        payment.status = Payment.Status.FAILED
        payment.raw_response = {"error": str(exc)}
        payment.save(
            update_fields=["status", "raw_response", "updated_at"]
        )
        raise

    authorization = (
        response.get("meta", {}).get("authorization", {})
    )
    payment.status = Payment.Status.PROCESSING
    payment.authorization_url = authorization.get("redirect", "")
    payment.raw_response = response
    payment.save(
        update_fields=[
            "status",
            "authorization_url",
            "raw_response",
            "updated_at",
        ]
    )
    return payment


@transaction.atomic
def finalize_successful_deposit(*, payment, transaction_data):
    payment = (
        Payment.objects
        .select_for_update()
        .select_related("scholar", "deposit")
        .get(pk=payment.pk)
    )

    if payment.status == Payment.Status.SUCCESSFUL:
        if payment.deposit_id is None:
            raise ValidationError(
                "Successful payment is missing its deposit."
            )
        return payment.deposit

    validate_verified_charge(
        payment=payment,
        verified_data=transaction_data,
    )

    deposit = create_successful_deposit(
        scholar=payment.scholar,
        amount=payment.amount,
        source=Deposit.Source.FLUTTERWAVE,
        reference=payment.reference,
        description="Flutterwave deposit",
        currency=payment.currency,
    )

    transaction_id = transaction_data.get("id")
    try:
        transaction_id = int(transaction_id)
    except (TypeError, ValueError):
        raise ValidationError(
            "Flutterwave verification did not return a transaction ID."
        )

    payment.status = Payment.Status.SUCCESSFUL
    payment.flutterwave_transaction_id = transaction_id
    payment.flutterwave_reference = str(
        transaction_data.get("flw_ref", "")
    )
    payment.deposit = deposit
    payment.completed_at = timezone.now()
    payment.raw_response = transaction_data
    payment.save(
        update_fields=[
            "status",
            "flutterwave_transaction_id",
            "flutterwave_reference",
            "deposit",
            "completed_at",
            "raw_response",
            "updated_at",
        ]
    )
    return deposit


def verify_and_finalize_payment(payment, flutterwave_transaction_id):
    response = FlutterwaveClient().verify_transaction(
        flutterwave_transaction_id
    )
    verified_data = response.get("data")
    if not isinstance(verified_data, dict):
        raise ValidationError(
            "Flutterwave verification returned no transaction data."
        )

    return finalize_successful_deposit(
        payment=payment,
        transaction_data=verified_data,
    )