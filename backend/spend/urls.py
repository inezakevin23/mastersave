from django.urls import path

from .views import (
    AllowancePlanDetailView,
    AllowancePlanListView,
    AllowanceReleaseDetailView,
    AllowanceReleaseListView,
)


urlpatterns = [
    path(
        "plans/",
        AllowancePlanListView.as_view(),
        name="allowance-plan-list",
    ),

    path(
        "plans/<uuid:pk>/",
        AllowancePlanDetailView.as_view(),
        name="allowance-plan-detail",
    ),

    path(
        "releases/",
        AllowanceReleaseListView.as_view(),
        name="allowance-release-list",
    ),

    path(
        "releases/<uuid:pk>/",
        AllowanceReleaseDetailView.as_view(),
        name="allowance-release-detail",
    ),

]