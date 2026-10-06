from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from savings.models import SavingsBucket
from spend.models import AllowanceRelease

from .models import Payout, PayoutDestination, Payment
from .payout_services import (
    create_allowance_payout,
    create_savings_withdrawal_payout,
)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "reference",
            "order_id",
            "amount",
            "currency",
            "payment_method",
            "status",
            "authorization_url",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields


class PaymentInitiateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=1,
    )


class PayoutDestinationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    account_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    masked_account = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()

    class Meta:
        model = PayoutDestination
        fields = [
            "id",
            "method",
            "beneficiary_name",
            "network",
            "phone_number",
            "bank_code",
            "branch_code",
            "account_number",
            "currency",
            "is_default",
            "masked_account",
            "masked_phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "masked_account",
            "masked_phone",
        ]

    def get_masked_account(self, destination):
        if not destination.account_number:
            return None
        return f"****{destination.account_number[-4:]}"

    def get_masked_phone(self, destination):
        if not destination.phone_number:
            return None
        return f"****{destination.phone_number[-4:]}"

    def validate_currency(self, value):
        currency = value.upper()
        if currency != "RWF":
            raise serializers.ValidationError(
                "Flutterwave payouts currently support RWF only."
            )
        return currency

    def validate(self, attrs):
        method = attrs.get("method")
        if method == PayoutDestination.Method.MOBILE_MONEY:
            network = attrs.get("network")
            if network not in {"MTN", "MPS"}:
                raise serializers.ValidationError(
                    {
                        "network": (
                            "Unsupported Rwanda mobile money network."
                        )
                    }
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        scholar = validated_data.pop("scholar")
        is_default = validated_data.get("is_default", False)
        if is_default:
            PayoutDestination.objects.filter(
                scholar=scholar,
                is_default=True,
            ).update(is_default=False)
        return PayoutDestination.objects.create(
            scholar=scholar,
            **validated_data,
        )


class PayoutSerializer(serializers.ModelSerializer):
    destination = PayoutDestinationSerializer(read_only=True)
    source_name = serializers.SerializerMethodField()

    class Meta:
        model = Payout
        fields = [
            "id",
            "kind",
            "status",
            "amount",
            "currency",
            "reference",
            "destination",
            "source_name",
            "allowance_release",
            "savings_bucket",
            "savings_transaction",
            "investment_account",
            "provider_reference",
            "provider_status",
            "fee",
            "failure_reason",
            "initiated_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_source_name(self, payout):
        if payout.allowance_release_id:
            return f"Week {payout.allowance_release.week_number}"
        if payout.savings_bucket_id:
            return payout.savings_bucket.name
        return "Investment"


class WithdrawalSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(
        choices=[
            ("SAVINGS", "Savings"),
            ("ALLOWANCE", "Allowance"),
        ],
    )
    source_id = serializers.UUIDField()
    destination_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )
    destination = PayoutDestinationSerializer(required=False)
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        min_value=1,
        required=False,
    )

    def validate(self, attrs):
        scholar = self.context["request"].user
        if attrs["source_type"] == "SAVINGS":
            bucket = SavingsBucket.objects.filter(
                pk=attrs["source_id"],
                scholar=scholar,
            ).first()
            if bucket is None:
                raise serializers.ValidationError(
                    {"source_id": "This savings bucket does not belong to you."}
                )
            if "amount" not in attrs:
                raise serializers.ValidationError(
                    {"amount": "This field is required for savings withdrawals."}
                )
            attrs["_bucket_instance"] = bucket
        else:
            release = AllowanceRelease.objects.filter(
                pk=attrs["source_id"],
                plan__scholar=scholar,
                status=AllowanceRelease.Status.SCHEDULED,
                scheduled_at__date__lte=timezone.localdate(),
            ).first()
            if release is None:
                raise serializers.ValidationError(
                    {
                        "source_id": (
                            "Only the current week's allowance can be withdrawn."
                        )
                    }
                )
            current_release = (
                AllowanceRelease.objects
                .filter(
                    plan=release.plan,
                    scheduled_at__date__lte=timezone.localdate(),
                )
                .order_by("-scheduled_at", "-week_number")
                .first()
            )
            if current_release is None or current_release.pk != release.pk:
                raise serializers.ValidationError(
                    {
                        "source_id": (
                            "Only the current week's allowance can be withdrawn."
                        )
                    }
                )
            if "amount" in attrs:
                raise serializers.ValidationError(
                    {"amount": "Allowance release amounts are fixed by the plan."}
                )
            attrs["_release_instance"] = release

        destination_id = attrs.get("destination_id")
        destination_data = attrs.get("destination")
        if bool(destination_id) == bool(destination_data):
            raise serializers.ValidationError(
                {
                    "destination": (
                        "Provide either destination_id or destination, not both."
                    )
                }
            )

        if destination_id:
            destination = PayoutDestination.objects.filter(
                pk=destination_id,
                scholar=scholar,
            ).first()
            if destination is None:
                raise serializers.ValidationError(
                    {
                        "destination_id": (
                            "This payout destination does not belong to you."
                        )
                    }
                )
            attrs["_destination_instance"] = destination

        return attrs

    def create(self, validated_data):
        source_type = validated_data.pop("source_type")
        source = (
            validated_data.pop("_bucket_instance", None)
            or validated_data.pop("_release_instance", None)
        )
        destination = validated_data.pop("_destination_instance", None)
        validated_data.pop("source_id")
        validated_data.pop("destination_id", None)
        destination_data = validated_data.pop("destination", None)

        if destination is None:
            destination_serializer = PayoutDestinationSerializer(
                data=destination_data,
                context=self.context,
            )
            destination_serializer.is_valid(raise_exception=True)
            destination = destination_serializer.save(
                scholar=self.context["request"].user
            )

        if source_type == "SAVINGS":
            return create_savings_withdrawal_payout(
                scholar=self.context["request"].user,
                bucket=source,
                destination=destination,
                amount=validated_data["amount"],
            )

        return create_allowance_payout(
            release=source,
            destination=destination,
        )
