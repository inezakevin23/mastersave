from django.contrib import admin

from .models import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "scholar",
        "amount",
        "currency",
        "source",
        "status",
        "confirmed_at",
        "created_at",
    ]

    list_filter = [
        "status",
        "source",
        "currency",
    ]

    search_fields = [
        "reference",
        "scholar__email",
        "scholar__first_name",
        "scholar__last_name",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]