from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from allocations.models import DepositAllocation
from allocations.services import (
    get_setup_status,
    setup_allocation,
)
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

        status = get_setup_status(self.user)

        self.assertEqual(
            status["latest_deposit_amount"],
            self.deposit.amount,
        )

        allocation = DepositAllocation.objects.get()

        self.assertEqual(
            allocation.deposit,
            self.deposit,
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

    def test_setup_uses_latest_unallocated_deposit(self):
        latest_deposit = Deposit.objects.create(
            scholar=self.user,
            amount=Decimal("1200000"),
            currency="RWF",
            source=Deposit.Source.ALLOWANCE,
            status=Deposit.Status.SUCCESSFUL,
            reference="TEST-DEP-SETUP-LATEST",
        )

        setup_allocation(
            **self.valid_setup()
        )

        allocation = DepositAllocation.objects.get()

        self.assertEqual(
            allocation.deposit,
            latest_deposit,
        )

        status = get_setup_status(self.user)

        self.assertEqual(
            status["latest_deposit_amount"],
            latest_deposit.amount,
        )

    def test_setup_status_reports_unallocated_amount(self):
        status = get_setup_status(self.user)

        self.assertTrue(
            status["has_unallocated_deposit"]
        )
        self.assertEqual(
            status["latest_deposit_amount"],
            self.deposit.amount,
        )

    def test_setup_status_reports_zero_without_successful_deposit(self):
        self.deposit.status = Deposit.Status.FAILED
        self.deposit.save(update_fields=["status"])

        status = get_setup_status(self.user)

        self.assertFalse(
            status["has_successful_deposit"]
        )
        self.assertEqual(
            status["latest_deposit_amount"],
            0,
        )

    def test_setup_requires_successful_unallocated_deposit(self):
        self.deposit.status = Deposit.Status.FAILED
        self.deposit.save(update_fields=["status"])

        with self.assertRaises(ValidationError) as context:
            setup_allocation(**self.valid_setup())

        self.assertEqual(
            context.exception.message_dict["deposit"],
            [
                "You do not have a successful "
                "unallocated deposit available."
            ],
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

    def test_each_deposit_can_have_its_own_active_plan(self):
        setup_allocation(
            **self.valid_setup()
        )

        Deposit.objects.create(
            scholar=self.user,
            amount=Decimal("1200000"),
            currency="RWF",
            source=Deposit.Source.ALLOWANCE,
            status=Deposit.Status.SUCCESSFUL,
            reference="TEST-DEP-SETUP-002",
        )

        setup_allocation(**self.valid_setup())

        self.assertEqual(
            DepositAllocation.objects.count(),
            2,
        )
        self.assertEqual(
            AllowancePlan.objects.filter(
                status=AllowancePlan.Status.ACTIVE
            ).count(),
            2,
        )
