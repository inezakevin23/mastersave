import os
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from .admin import PayoutAdmin
from .flutterwave import (
    FlutterwaveClient,
    FlutterwaveError,
    FlutterwaveTransportError,
)
from .mode import is_demo_mode
from .models import Payout
from .serializers import WithdrawalSerializer
from .views import WithdrawalView, flutterwave_redirect
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


class DemoPayoutAdminTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    @patch.dict(os.environ, {"FLUTTERWAVE_MODE": "test"})
    def test_demo_actions_enabled_only_in_debug_test_mode(self):
        self.assertTrue(is_demo_mode())

    @override_settings(DEBUG=False)
    @patch.dict(os.environ, {"FLUTTERWAVE_MODE": "test"})
    def test_demo_actions_disabled_when_debug_is_off(self):
        self.assertFalse(is_demo_mode())

    @override_settings(DEBUG=True)
    @patch.dict(os.environ, {"FLUTTERWAVE_MODE": "test"})
    def test_demo_actions_are_visible_in_payout_admin(self):
        request = RequestFactory().get("/admin/payments/payout/")
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            has_perm=lambda permission: True,
        )

        actions = PayoutAdmin(Payout, admin.site).get_actions(request)

        self.assertIn("demo_mark_successful", actions)
        self.assertIn("demo_mark_failed", actions)

    @override_settings(DEBUG=True)
    @patch.dict(os.environ, {"FLUTTERWAVE_MODE": "test"})
    def test_demo_status_field_exposes_controlled_terminal_choices(self):
        payout_admin = PayoutAdmin(Payout, admin.site)
        request = RequestFactory().get("/admin/payments/payout/")
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            has_perm=lambda permission: True,
        )

        readonly_fields = payout_admin.get_readonly_fields(
            request,
            obj=SimpleNamespace(status=Payout.Status.REQUESTED),
        )
        status_field = payout_admin.formfield_for_choice_field(
            Payout._meta.get_field("status"),
            request,
        )

        self.assertNotIn("status", readonly_fields)
        self.assertIn(
            (Payout.Status.SUCCESSFUL, "Demo: Successful"),
            list(status_field.choices),
        )
        self.assertIn(
            (Payout.Status.FAILED, "Demo: Failed"),
            list(status_field.choices),
        )


class PaymentEndpointTests(SimpleTestCase):
    @patch("payments.views.is_demo_mode", return_value=True)
    @patch("payments.views.send_payout_to_flutterwave")
    @patch("payments.views.WithdrawalSerializer")
    @patch("payments.views.PayoutSerializer")
    def test_demo_withdrawal_does_not_send_transfer(
        self,
        payout_serializer_class,
        withdrawal_serializer_class,
        send_transfer,
        demo_mode,
    ):
        scholar = SimpleNamespace(is_authenticated=True)
        payout = SimpleNamespace(
            provider_status="",
            raw_response={},
            save=Mock(),
        )
        withdrawal_serializer = withdrawal_serializer_class.return_value
        withdrawal_serializer.save.return_value = payout
        payout_serializer_class.return_value.data = {"status": "REQUESTED"}

        request = APIRequestFactory().post(
            "/api/payments/withdrawals/",
            data={},
            format="json",
        )
        force_authenticate(request, user=scholar)

        response = WithdrawalView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["demo_mode"])
        send_transfer.assert_not_called()

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

    @patch("payments.serializers.create_allowance_payout")
    def test_allowance_withdrawal_uses_server_release_amount(
        self,
        create_payout,
    ):
        scholar = SimpleNamespace(id="scholar-id")
        release = SimpleNamespace(id="release-id")
        destination = SimpleNamespace(id="destination-id")
        request = SimpleNamespace(user=scholar)
        serializer = WithdrawalSerializer(
            context={"request": request}
        )

        payout = serializer.create(
            {
                "source_type": "ALLOWANCE",
                "source_id": release.id,
                "_release_instance": release,
                "_destination_instance": destination,
            }
        )

        self.assertIs(payout, create_payout.return_value)
        create_payout.assert_called_once_with(
            release=release,
            destination=destination,
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
