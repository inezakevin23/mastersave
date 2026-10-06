from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("spend", "0004_delete_expense"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="allowanceplan",
            name="one_active_allowance_plan_per_scholar",
        ),
    ]
