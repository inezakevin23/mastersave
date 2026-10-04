from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from allocations.models import DepositAllocation
from deposits.models import Deposit
from investments.models import (
    InvestmentProduct,
    InvestmentRequest,
)
from investments.services import (
    create_investment_request,
    get_available_grow_amount,
    get_invested_grow_amount,
    get_reserved_grow_amount,
)


class GrowAllocationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="scholar@test.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Scholar",
            phone="+250788000000",
        )

        self.deposit = Deposit.objects.create(
            scholar=self.user,
            amount=Decimal("1200000"),
            currency="RWF",
            source=Deposit.Source.ALLOWANCE,
            status=Deposit.Status.SUCCESSFUL,
            reference="TEST-DEP-001",
        )

        self.allocation = (
            DepositAllocation.objects.create(
                deposit=self.deposit,
                spend_amount=Decimal("600000"),
                save_amount=Decimal("480000"),
                grow_amount=Decimal("120000"),
            )
        )

        self.product = (
            InvestmentProduct.objects.create(
                name="Test Investment",
                partner_name="Test Partner",
                description="Test product",
                currency="RWF",
                minimum_amount=Decimal("50000"),
                annual_rate=Decimal("7"),
                term_months=12,
                risk_level=(
                    InvestmentProduct.RiskLevel.LOW
                ),
                status=(
                    InvestmentProduct.Status.ACTIVE
                ),
            )
        )

    def test_initial_grow_available(self):
        self.assertEqual(
            get_reserved_grow_amount(
                self.allocation
            ),
            0,
        )

        self.assertEqual(
            get_invested_grow_amount(
                self.allocation
            ),
            0,
        )

        self.assertEqual(
            get_available_grow_amount(
                self.allocation
            ),
            Decimal("120000"),
        )

    def test_pending_request_reserves_money(self):
        create_investment_request(
            scholar=self.user,
            allocation=self.allocation,
            product=self.product,
            amount=Decimal("50000"),
        )

        self.assertEqual(
            get_reserved_grow_amount(
                self.allocation
            ),
            Decimal("50000"),
        )

        self.assertEqual(
            get_invested_grow_amount(
                self.allocation
            ),
            0,
        )

        self.assertEqual(
            get_available_grow_amount(
                self.allocation
            ),
            Decimal("70000"),
        )

    def test_cannot_exceed_available_grow(self):
        create_investment_request(
            scholar=self.user,
            allocation=self.allocation,
            product=self.product,
            amount=Decimal("70000"),
        )

        with self.assertRaises(
            ValidationError
        ):
            create_investment_request(
                scholar=self.user,
                allocation=self.allocation,
                product=self.product,
                amount=Decimal("60000"),
            )

    def test_requests_are_not_allowed_below_minimum(self):
        with self.assertRaises(
            ValidationError
        ):
            create_investment_request(
                scholar=self.user,
                allocation=self.allocation,
                product=self.product,
                amount=Decimal("10000"),
            )