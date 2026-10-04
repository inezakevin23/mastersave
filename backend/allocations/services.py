from django.core.exceptions import ValidationError
from django.db import transaction

from deposits.models import Deposit
from savings.models import SavingsBucket
from savings.services import create_contribution
from spend.models import AllowancePlan
from spend.services import create_allowance_releases

from .models import DepositAllocation
from .validators import validate_allocation_amounts


@transaction.atomic
def setup_allocation(
    *,
    scholar,
    deposit,
    spend_amount,
    save_amount,
    grow_amount,
    weekly_amount,
    number_of_weeks,
    start_date,
    release_weekday,
    release_time,
    goal_lock_amount,
    goal_lock_target_amount,
    goal_lock_target_date=None,
    emergency_save_amount,
    goal_lock_name="Goal Lock",
    emergency_save_name="Emergency Save",
):
    """
    Atomically creates the financial setup for
    a successful deposit.

    Creates:
        - DepositAllocation
        - AllowancePlan
        - AllowanceReleases
        - Goal Lock bucket
        - Emergency Save bucket
        - Initial savings contributions

    If any operation fails, the entire setup is
    rolled back.
    """

    # -------------------------------------------------
    # 1. Lock the deposit
    # -------------------------------------------------

    locked_deposit = (
        Deposit.objects
        .select_for_update()
        .select_related("scholar")
        .get(pk=deposit.pk)
    )

    # -------------------------------------------------
    # 2. Ownership validation
    # -------------------------------------------------

    if locked_deposit.scholar_id != scholar.id:
        raise ValidationError(
            {
                "deposit": (
                    "This deposit does not "
                    "belong to you."
                )
            }
        )

    # -------------------------------------------------
    # 3. Deposit status validation
    # -------------------------------------------------

    if locked_deposit.status != (
        Deposit.Status.SUCCESSFUL
    ):
        raise ValidationError(
            {
                "deposit": (
                    "Only successful deposits "
                    "can be allocated."
                )
            }
        )

    # -------------------------------------------------
    # 4. Prevent duplicate allocation
    # -------------------------------------------------

    if hasattr(locked_deposit, "allocation"):
        raise ValidationError(
            {
                "deposit": (
                    "This deposit has already "
                    "been allocated."
                )
            }
        )

    # -------------------------------------------------
    # 5. Validate main allocation
    # -------------------------------------------------

    validate_allocation_amounts(
        deposit_amount=locked_deposit.amount,
        spend_amount=spend_amount,
        save_amount=save_amount,
        grow_amount=grow_amount,
    )

    # -------------------------------------------------
    # 6. Validate Save split
    # -------------------------------------------------

    if (
        goal_lock_amount
        + emergency_save_amount
        != save_amount
    ):
        raise ValidationError(
            {
                "save": (
                    "Goal Lock amount plus "
                    "Emergency Save amount must "
                    "equal the Save allocation."
                )
            }
        )

    if goal_lock_amount < 0:
        raise ValidationError(
            {
                "goal_lock_amount": (
                    "Goal Lock amount cannot "
                    "be negative."
                )
            }
        )

    if emergency_save_amount < 0:
        raise ValidationError(
            {
                "emergency_save_amount": (
                    "Emergency Save amount "
                    "cannot be negative."
                )
            }
        )

    if save_amount > 0:
        if (
            goal_lock_amount == 0
            and emergency_save_amount == 0
        ):
            raise ValidationError(
                {
                    "save": (
                        "Save allocation must be "
                        "assigned to at least one "
                        "savings bucket."
                    )
                }
            )

    # -------------------------------------------------
    # 7. Prevent multiple active plans
    # -------------------------------------------------

    active_plan_exists = (
        AllowancePlan.objects
        .filter(
            scholar=scholar,
            status=AllowancePlan.Status.ACTIVE,
        )
        .exists()
    )

    if active_plan_exists:
        raise ValidationError(
            {
                "spend": (
                    "You already have an active "
                    "allowance plan."
                )
            }
        )

    # -------------------------------------------------
    # 8. Create allocation
    # -------------------------------------------------

    allocation = (
        DepositAllocation.objects.create(
            deposit=locked_deposit,
            spend_amount=spend_amount,
            save_amount=save_amount,
            grow_amount=grow_amount,
            status=(
                DepositAllocation.Status.CONFIRMED
            ),
        )
    )

    # -------------------------------------------------
    # 9. Create weekly Spend plan
    # -------------------------------------------------

    plan = AllowancePlan.objects.create(
        scholar=scholar,
        source_allocation=allocation,
        weekly_amount=weekly_amount,
        number_of_weeks=number_of_weeks,
        start_date=start_date,
        release_weekday=release_weekday,
        release_time=release_time,
        status=AllowancePlan.Status.ACTIVE,
    )

    create_allowance_releases(plan)

    # -------------------------------------------------
    # 10. Create Goal Lock
    # -------------------------------------------------

    goal_bucket = None

    if goal_lock_amount > 0:
        goal_bucket, _ = (
            SavingsBucket.objects.get_or_create(
                scholar=scholar,
                name=goal_lock_name,
                defaults={
                    "bucket_type": (
                        SavingsBucket
                        .BucketType
                        .GOAL_LOCK
                    ),
                    "target_amount": (
                        goal_lock_target_amount
                    ),
                    "target_date": (
                        goal_lock_target_date
                    ),
                    "status": (
                        SavingsBucket
                        .Status
                        .ACTIVE
                    ),
                },
            )
        )

        if (
            goal_bucket.bucket_type
            != SavingsBucket.BucketType.GOAL_LOCK
        ):
            raise ValidationError(
                {
                    "goal_lock_name": (
                        "A savings bucket with "
                        "this name already exists "
                        "with another bucket type."
                    )
                }
            )

        create_contribution(
            bucket=goal_bucket,
            allocation=allocation,
            amount=goal_lock_amount,
            description=(
                "Initial Goal Lock allocation"
            ),
        )

    # -------------------------------------------------
    # 11. Create Emergency Save
    # -------------------------------------------------

    emergency_bucket = None

    if emergency_save_amount > 0:
        emergency_bucket, _ = (
            SavingsBucket.objects.get_or_create(
                scholar=scholar,
                name=emergency_save_name,
                defaults={
                    "bucket_type": (
                        SavingsBucket
                        .BucketType
                        .EMERGENCY
                    ),
                    "target_amount": None,
                    "target_date": None,
                    "status": (
                        SavingsBucket
                        .Status
                        .ACTIVE
                    ),
                },
            )
        )

        if (
            emergency_bucket.bucket_type
            != SavingsBucket
            .BucketType
            .EMERGENCY
        ):
            raise ValidationError(
                {
                    "emergency_save_name": (
                        "A savings bucket with "
                        "this name already exists "
                        "with another bucket type."
                    )
                }
            )

        create_contribution(
            bucket=emergency_bucket,
            allocation=allocation,
            amount=emergency_save_amount,
            description=(
                "Initial Emergency Save allocation"
            ),
        )

    # -------------------------------------------------
    # 12. Return complete setup
    # -------------------------------------------------

    return {
        "allocation": allocation,
        "plan": plan,
        "goal_bucket": goal_bucket,
        "emergency_bucket": emergency_bucket,
    }