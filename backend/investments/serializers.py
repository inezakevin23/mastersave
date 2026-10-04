from rest_framework import serializers

from allocations.models import DepositAllocation

from .models import (
    InvestmentAccount,
    InvestmentProduct,
    InvestmentRequest,
    InvestmentTransaction,
)
from .services import (
    create_investment_request,
)


class InvestmentProductSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = InvestmentProduct

        fields = [
            "id",
            "name",
            "partner_name",
            "description",
            "currency",
            "minimum_amount",
            "annual_rate",
            "term_months",
            "risk_level",
            "risk_information",
            "status",
        ]

        read_only_fields = fields


class InvestmentRequestSerializer(
    serializers.ModelSerializer
):
    source_allocation = (
        serializers.PrimaryKeyRelatedField(
            queryset=DepositAllocation.objects.all()
        )
    )

    product = serializers.PrimaryKeyRelatedField(
        queryset=InvestmentProduct.objects.all()
    )

    class Meta:
        model = InvestmentRequest

        fields = [
            "id",
            "source_allocation",
            "product",
            "amount",
            "status",
            "reference",
            "rejection_reason",
            "requested_at",
            "reviewed_at",
            "completed_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "reference",
            "rejection_reason",
            "requested_at",
            "reviewed_at",
            "completed_at",
        ]

    def create(self, validated_data):
        return create_investment_request(
            scholar=self.context[
                "request"
            ].user,
            allocation=validated_data[
                "source_allocation"
            ],
            product=validated_data[
                "product"
            ],
            amount=validated_data[
                "amount"
            ],
        )


class InvestmentTransactionSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = InvestmentTransaction

        fields = [
            "id",
            "transaction_type",
            "amount",
            "reference",
            "description",
            "status",
            "occurred_at",
            "created_at",
        ]

        read_only_fields = fields


class InvestmentAccountSerializer(
    serializers.ModelSerializer
):
    balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )

    principal = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )

    projected_return = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        read_only=True,
    )

    annual_rate = serializers.DecimalField(
        source="product.annual_rate",
        max_digits=7,
        decimal_places=4,
        read_only=True,
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    partner_name = serializers.CharField(
        source="product.partner_name",
        read_only=True,
    )

    class Meta:
        model = InvestmentAccount

        fields = [
            "id",
            "product_name",
            "partner_name",
            "annual_rate",
            "principal",
            "balance",
            "projected_return",
            "status",
            "started_at",
            "maturity_date",
            "partner_account_reference",
        ]

        read_only_fields = fields