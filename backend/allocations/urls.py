from django.urls import path

from .views import (
    AllocationDetailView,
    AllocationListView,
    AllocationSetupView,
    AllocationSetupStatusView,
)


urlpatterns = [
    path(
        "",
        AllocationListView.as_view(),
        name="allocation-list",
    ),

    path(
        "setup/",
        AllocationSetupView.as_view(),
        name="allocation-setup",
    ),

    path(
        "<uuid:pk>/",
        AllocationDetailView.as_view(),
        name="allocation-detail",
    ),
    path(
        "status/",
        AllocationSetupStatusView.as_view(),
        name="allocation-setup-status",
    ),
]