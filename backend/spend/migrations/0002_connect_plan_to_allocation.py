from django.db import migrations, models
import django.db.models.deletion


def link_existing_plans(apps, schema_editor):
    AllowancePlan = apps.get_model("spend", "AllowancePlan")
    DepositAllocation = apps.get_model(
        "allocations",
        "DepositAllocation",
    )
    database = schema_editor.connection.alias

    for plan in AllowancePlan.objects.using(database).all():
        allocations = list(
            DepositAllocation.objects.using(database)
            .filter(
                deposit__scholar_id=plan.scholar_id,
                spend_amount=plan.total_amount,
                status__in=["CONFIRMED", "LOCKED"],
            )
            .exclude(spend_plan__isnull=False)
        )

        if len(allocations) != 1:
            raise RuntimeError(
                f"Cannot uniquely link allowance plan {plan.pk} "
                f"to an allocation: found {len(allocations)} matches."
            )

        plan.source_allocation_id = allocations[0].pk
        plan.save(
            using=database,
            update_fields=["source_allocation"],
        )


def restore_plan_amounts(apps, schema_editor):
    AllowancePlan = apps.get_model("spend", "AllowancePlan")
    database = schema_editor.connection.alias

    for plan in AllowancePlan.objects.using(database).select_related(
        "source_allocation"
    ):
        plan.total_amount = plan.source_allocation.spend_amount
        plan.save(
            using=database,
            update_fields=["total_amount"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("allocations", "0001_initial"),
        ("spend", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="allowanceplan",
            name="source_allocation",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="spend_plan",
                to="allocations.depositallocation",
            ),
        ),
        migrations.RunPython(
            link_existing_plans,
            restore_plan_amounts,
        ),
        migrations.AlterField(
            model_name="allowanceplan",
            name="source_allocation",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="spend_plan",
                to="allocations.depositallocation",
            ),
        ),
        migrations.RemoveField(
            model_name="allowanceplan",
            name="total_amount",
        ),
        migrations.AddConstraint(
            model_name="allowanceplan",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="ACTIVE"),
                fields=("scholar",),
                name="one_active_allowance_plan_per_scholar",
            ),
        ),
    ]
