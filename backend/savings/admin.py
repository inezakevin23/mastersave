from django.contrib import admin

from .models import (
    SavingsBucket,
    SavingsTransaction,
)


class SavingsTransactionInline(
    admin.TabularInline
):
    model = SavingsTransaction
    extra = 0

    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
    ]


@admin.register(SavingsBucket)
class SavingsBucketAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "scholar",
        "bucket_type",
        "target_amount",
        "balance_display",
        "status",
        "created_at",
    ]

    list_filter = [
        "bucket_type",
        "status",
    ]

    search_fields = [
        "name",
        "scholar__email",
        "scholar__first_name",
        "scholar__last_name",
    ]

    inlines = [
        SavingsTransactionInline,
    ]

    def balance_display(self, obj):
        return obj.balance

    balance_display.short_description = "Balance"


@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "bucket",
        "transaction_type",
        "amount",
        "status",
        "source_allocation",
        "confirmed_at",
        "created_at",
    ]

    list_filter = [
        "transaction_type",
        "status",
    ]

    search_fields = [
        "reference",
        "bucket__name",
        "bucket__scholar__email",
    ]

    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
    ]