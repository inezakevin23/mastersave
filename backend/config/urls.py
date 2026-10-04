from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        "api/auth/",
        include("accounts.urls"),
    ),
    path(
        "api/spend/",
        include("spend.urls"),
    ),
    path(
        "api/dashboard/",
        include("dashboard.urls"),
    ),
    path(
        "api/allocations/",
        include("allocations.urls"),
    ),
]
