from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


def _decimal_amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({"amount": "Amount must be a valid number."})

    if not amount.is_finite():
        raise ValidationError({"amount": "Amount must be a valid number."})

    return amount


def validate_rwf_amount(amount):
    if _decimal_amount(amount) <= 0:
        raise ValidationError(
            {"amount": "Amount must be greater than zero."}
        )


def validate_verified_charge(*, payment, verified_data):
    status = str(verified_data.get("status", "")).lower()
    currency = str(verified_data.get("currency", "")).upper()
    tx_ref = str(verified_data.get("tx_ref", ""))
    amount = _decimal_amount(verified_data.get("amount", 0))

    if status != "successful":
        raise ValidationError(
            "Flutterwave transaction was not successful."
        )

    if currency != payment.currency.upper():
        raise ValidationError(
            "Flutterwave currency does not match."
        )

    if tx_ref != payment.reference:
        raise ValidationError(
            "Flutterwave transaction reference does not match."
        )

    if amount != payment.amount:
        raise ValidationError(
            "Flutterwave transaction amount does not match."
        )


def validate_verified_transfer(*, payout, verified_data):
    status = str(verified_data.get("status", "")).upper()
    currency = str(verified_data.get("currency", "")).upper()
    reference = str(verified_data.get("reference", ""))
    amount = _decimal_amount(verified_data.get("amount", 0))

    if status != "SUCCESSFUL":
        raise ValidationError(
            "Flutterwave transfer is not successful."
        )

    if currency != payout.currency.upper():
        raise ValidationError(
            "Flutterwave transfer currency does not match."
        )

    if reference != payout.reference:
        raise ValidationError(
            "Flutterwave transfer reference does not match."
        )

    if amount != payout.amount:
        raise ValidationError(
            "Flutterwave transfer amount does not match."
        )