from decimal import Decimal

from django.db import migrations


def seed_demo_products(apps, schema_editor):
    InvestmentProduct = apps.get_model("investments", "InvestmentProduct")
    products = [
        {
            "name": "RNIT Iterambere Fund (Demo)",
            "partner_name": "RNIT (prototype listing)",
            "description": (
                "Prototype listing inspired by the RNIT Iterambere Fund. "
                "This sample is for demonstrating the MasterSave Grow flow; "
                "terms and rates are illustrative and are not an offer."
            ),
            "minimum_amount": Decimal("10000"),
            "annual_rate": Decimal("8.0000"),
            "term_months": 12,
            "risk_level": "MEDIUM",
            "risk_information": (
                "Demo values only. Actual product terms, eligibility, "
                "fees, and returns must be confirmed with the provider. "
                "Returns are not guaranteed."
            ),
        },
        {
            "name": "Treasury Growth Fund (Demo)",
            "partner_name": "MasterSave prototype",
            "description": (
                "Sample fixed-term investment product for prototype "
                "demonstrations. This is not a real offer."
            ),
            "minimum_amount": Decimal("25000"),
            "annual_rate": Decimal("6.0000"),
            "term_months": 6,
            "risk_level": "LOW",
            "risk_information": (
                "Illustrative demo values only; returns are not guaranteed."
            ),
        },
        {
            "name": "Balanced Growth Fund (Demo)",
            "partner_name": "MasterSave prototype",
            "description": (
                "Sample diversified investment product for prototype "
                "demonstrations. This is not a real offer."
            ),
            "minimum_amount": Decimal("50000"),
            "annual_rate": Decimal("10.0000"),
            "term_months": 24,
            "risk_level": "HIGH",
            "risk_information": (
                "Illustrative demo values only; capital and returns may vary."
            ),
        },
    ]

    for product in products:
        InvestmentProduct.objects.update_or_create(
            name=product["name"],
            defaults={
                **product,
                "currency": "RWF",
                "status": "ACTIVE",
            },
        )


class Migration(migrations.Migration):
    dependencies = [("investments", "0001_initial")]

    operations = [
        migrations.RunPython(seed_demo_products, migrations.RunPython.noop),
    ]
