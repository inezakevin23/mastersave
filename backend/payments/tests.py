import os
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase

from .flutterwave import (
    FlutterwaveClient,
    FlutterwaveError,
    FlutterwaveTransportError,
)
from .serializers import WithdrawalSerializer
from .views import flutterwave_redirect
from .validators import (
    validate_rwf_amount,
    validate_verified_charge,
    validate_verified_transfer,
)


class PaymentValidatorTests(SimpleTestCase):
    def setUp(self):
        self.payment = SimpleNamespace(
            amount=Decimal("1000"),
            currency="RWF",
            reference="payment-ref",
        )
        self.payout = SimpleNamespace(
            amount=Decimal("1000"),
            currency="RWF",
            reference="payout-ref",
        )

    def test_rwf_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            validate_rwf_amount(0)

    def test_verified_charge_must_match_expected_payment(self):
        validate_verified_charge(
            payment=self.payment,
            verified_data={
                "status": "successful",
                "currency": "RWF",
                "tx_ref": "payment-ref",
                "amount": "1000",
            },
        )

        with self.assertRaises(ValidationError):
            validate_verified_charge(
                payment=self.payment,
                verified_data={
                    "status": "successful",
                    "currency": "RWF",
                    "tx_ref": "different-ref",
                    "amount": "1000",
                },
            )

    def test_verified_transfer_must_match_expected_payout(self):
        validate_verified_transfer(
            payout=self.payout,
            verified_data={
                "status": "SUCCESSFUL",
                "currency": "RWF",
                "reference": "payout-ref",
                "amount": "1000",
            },
        )

        with self.assertRaises(ValidationError):
            validate_verified_transfer(
                payout=self.payout,
                verified_data={
                    "status": "FAILED",
                    "currency": "RWF",
                    "reference": "payout-ref",
                    "amount": "1000",
                },
            )


class FlutterwaveClientTests(SimpleTestCase):
    @patch.dict(
        os.environ,
        {
            "FLUTTERWAVE_MODE": "test",
            "FLUTTERWAVE_SECRET_KEY": "FLWSECK_TEST-test-secret",
            "FLUTTERWAVE_PUBLIC_KEY": "FLWPUBK_TEST-test-public",
            "FLUTTERWAVE_BASE_URL": "https://api.example.com/",
            "FLUTTERWAVE_REDIRECT_URL": "https://app.example.com/return",
        },
    )
    @patch("payments.flutterwave.requests.request")
    def test_charge_uses_server_key_and_rwanda_payload(
        self,
        request,
    ):
        response = Mock()
        response.ok = True
        response.json.return_value = {"status": "success"}
        request.return_value = response

        client = FlutterwaveClient()
        result = client.charge_rwanda_mobile_money(
            amount=1000,
            email="scholar@example.com",
            phone_number="250780000000",
            fullname="Test Scholar",
            tx_ref="payment-ref",
            order_id="order-ref",
        )

        self.assertEqual(result, {"status": "success"})
        request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/v3/charges?type=mobile_money_rwanda",
            headers={
                "Authorization": "Bearer FLWSECK_TEST-test-secret",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
            json={
                "amount": 1000,
                "currency": "RWF",
                "email": "scholar@example.com",
                "tx_ref": "payment-ref",
                "order_id": "order-ref",
                "phone_number": "250780000000",
                "fullname": "Test Scholar",
                "redirect_url": "https://app.example.com/return",
            },
        )

    @patch.dict(
        os.environ,
        {
            "FLUTTERWAVE_MODE": "test",
            "FLUTTERWAVE_SECRET_KEY": "FLWSECK-live-secret",
        },
    )
    def test_test_mode_rejects_live_key(self):
        with self.assertRaises(FlutterwaveError):
            FlutterwaveClient()

    @patch.dict(
        os.environ,
        {
            "FLUTTERWAVE_MODE": "test",
            "FLUTTERWAVE_SECRET_KEY": "FLWSECK_TEST-test-secret",
            "FLUTTERWAVE_REDIRECT_URL": "",
        },
    )
    def test_charge_requires_a_return_url(self):
        client = FlutterwaveClient()
        with self.assertRaises(FlutterwaveError):
            client.charge_rwanda_mobile_money(
                amount=1000,
                email="scholar@example.com",
                phone_number="250780000000",
                fullname="Test Scholar",
                tx_ref="payment-ref",
                order_id="order-ref",
            )


class PaymentEndpointTests(SimpleTestCase):
    @patch("payments.serializers.create_savings_withdrawal_payout")
    def test_withdrawal_serializer_maps_savings_bucket(self, create_payout):
        scholar = SimpleNamespace(id="scholar-id")
        bucket = SimpleNamespace(id="bucket-id")
        destination = SimpleNamespace(id="destination-id")
        request = SimpleNamespace(user=scholar)
        serializer = WithdrawalSerializer(
            context={"request": request}
        )

        payout = serializer.create(
            {
                "source_type": "SAVINGS",
                "source_id": bucket.id,
                "destination_id": destination.id,
                "amount": Decimal("1000"),
                "_bucket_instance": bucket,
                "_destination_instance": destination,
            }
        )

        self.assertIs(payout, create_payout.return_value)
        create_payout.assert_called_once_with(
            scholar=scholar,
            bucket=bucket,
            destination=destination,
            amount=Decimal("1000"),
        )

    def test_redirect_requires_transaction_reference_and_id(self):
        request = RequestFactory().get(
            "/api/payments/flutterwave/redirect/"
        )

        response = flutterwave_redirect(request)

        self.assertEqual(response.status_code, 400)

    @patch("payments.views.verify_and_finalize_payment")
    @patch("payments.views.Payment.objects.filter")
    def test_redirect_verifies_transaction_before_confirming(
        self,
        filter_payments,
        verify_payment,
    ):
        payment = SimpleNamespace(reference="payment-ref")
        deposit = SimpleNamespace(id="deposit-id")
        filter_payments.return_value.first.return_value = payment
        verify_payment.return_value = deposit
        request = RequestFactory().get(
            "/api/payments/flutterwave/redirect/"
            "?transaction_id=123&tx_ref=payment-ref&status=successful"
        )

        response = flutterwave_redirect(request)

        self.assertEqual(response.status_code, 200)
        verify_payment.assert_called_once_with(
            payment=payment,
            flutterwave_transaction_id="123",
        )

    @patch("payments.views.verify_and_finalize_payment")
    @patch("payments.views.Payment.objects.filter")
    def test_redirect_does_not_confirm_unverified_transaction(
        self,
        filter_payments,
        verify_payment,
    ):
        payment = SimpleNamespace(reference="payment-ref")
        filter_payments.return_value.first.return_value = payment
        verify_payment.side_effect = FlutterwaveTransportError("offline")
        request = RequestFactory().get(
            "/api/payments/flutterwave/redirect/"
            "?transaction_id=123&tx_ref=payment-ref"
        )

        response = flutterwave_redirect(request)

        self.assertEqual(response.status_code, 502)
