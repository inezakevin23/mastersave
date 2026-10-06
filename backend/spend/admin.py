from django.contrib import admin

from .models import (
    AllowancePlan,
    AllowanceRelease,
)


class AllowanceReleaseInline(
    admin.TabularInline
):
    model = AllowanceRelease

    extra = 0

    readonly_fields = [
        "scheduled_at",
        "released_at",
    ]


@admin.register(AllowancePlan)
class AllowancePlanAdmin(admin.ModelAdmin):
    list_display = [
        "scholar",
        "total_amount",
        "weekly_amount",
        "number_of_weeks",
        "start_date",
        "status",
    ]

    list_filter = [
        "status",
        "number_of_weeks",
    ]

    search_fields = [
        "scholar__email",
        "scholar__first_name",
        "scholar__last_name",
    ]

    inlines = [
        AllowanceReleaseInline,
    ]


@admin.register(AllowanceRelease)
class AllowanceReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "plan",
        "week_number",
        "amount",
        "scheduled_at",
        "released_at",
        "status",
    ]

    list_filter = [
        "status",
    ]

    search_fields = [
        "plan__scholar__email",
    ]


