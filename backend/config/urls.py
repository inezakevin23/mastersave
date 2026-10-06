from django.contrib import admin
from django.urls import include, path
from .views import health_check

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
    path(
        "api/savings/",
        include("savings.urls"),
    ),
    path(
        "api/investments/",
        include("investments.urls"),
    ),
    path(
        "api/payments/",
        include("payments.urls"),
    ),
    path(
        "health/",
        health_check,
    )
]
