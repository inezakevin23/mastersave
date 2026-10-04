from django.contrib import admin

from .models import ScholarProfile


@admin.register(ScholarProfile)
class ScholarProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "institution",
        "country",
        "verification_status",
        "created_at",
    ]

    list_filter = [
        "verification_status",
        "country",
        "institution",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "scholar_id",
        "institution",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]