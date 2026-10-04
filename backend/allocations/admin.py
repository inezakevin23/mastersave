from django.contrib import admin

from .models import DepositAllocation


@admin.register(DepositAllocation)
class DepositAllocationAdmin(admin.ModelAdmin):
    list_display = [
        "deposit",
        "spend_amount",
        "save_amount",
        "grow_amount",
        "total_allocated",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
    ]

    search_fields = [
        "deposit__reference",
        "deposit__scholar__email",
        "deposit__scholar__first_name",
        "deposit__scholar__last_name",
    ]

    readonly_fields = [
        "total_allocated",
        "created_at",
        "updated_at",
    ]