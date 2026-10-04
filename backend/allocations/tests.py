from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from allocations.models import DepositAllocation
from allocations.services import setup_allocation
from deposits.models import Deposit
from savings.models import SavingsBucket
from spend.models import AllowancePlan
from datetime import date, time


class AllocationSetupTestCase(TestCase):

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
            reference="TEST-DEP-SETUP",
        )

    def valid_setup(self):
        return {
            "scholar": self.user,

            "deposit": self.deposit,

            "spend_amount": Decimal("600000"),
            "save_amount": Decimal("480000"),
            "grow_amount": Decimal("120000"),

            "weekly_amount": Decimal("50000"),
            "number_of_weeks": 12,

            "start_date": date(
                2026,
                10,
                5,
            ),

            "release_weekday": 0,
            "release_time": time(
                9,
                0,
            ),

            "goal_lock_amount": Decimal(
                "360000"
            ),

            "goal_lock_target_amount": Decimal(
                "500000"
            ),

            "emergency_save_amount": Decimal(
                "120000"
            ),
        }

    def test_successful_setup_creates_everything(self):
        setup_allocation(
            **self.valid_setup()
        )

        self.assertEqual(
            DepositAllocation.objects.count(),
            1,
        )

        self.assertEqual(
            AllowancePlan.objects.count(),
            1,
        )

        plan = AllowancePlan.objects.first()

        self.assertEqual(
            plan.releases.count(),
            12,
        )

        self.assertEqual(
            SavingsBucket.objects.count(),
            2,
        )

    def test_save_split_must_equal_save_allocation(self):
        data = self.valid_setup()

        data["goal_lock_amount"] = Decimal(
            "300000"
        )

        with self.assertRaises(
            ValidationError
        ):
            setup_allocation(**data)

        self.assertEqual(
            DepositAllocation.objects.count(),
            0,
        )

        self.assertEqual(
            AllowancePlan.objects.count(),
            0,
        )

        self.assertEqual(
            SavingsBucket.objects.count(),
            0,
        )

    def test_allocation_must_equal_deposit(self):
        data = self.valid_setup()

        data["grow_amount"] = Decimal(
            "100000"
        )

        with self.assertRaises(
            ValidationError
        ):
            setup_allocation(**data)

        self.assertEqual(
            DepositAllocation.objects.count(),
            0,
        )

    def test_only_one_active_plan(self):
        setup_allocation(
            **self.valid_setup()
        )

        second_deposit = Deposit.objects.create(
            scholar=self.user,
            amount=Decimal("1200000"),
            currency="RWF",
            source=Deposit.Source.ALLOWANCE,
            status=Deposit.Status.SUCCESSFUL,
            reference="TEST-DEP-SETUP-002",
        )

        data = self.valid_setup()

        data["deposit"] = second_deposit

        with self.assertRaises(
            ValidationError
        ):
            setup_allocation(**data)

        self.assertEqual(
            DepositAllocation.objects.count(),
            1,
        )