from django.urls import path

from .views import (
    AllowancePlanDetailView,
    AllowancePlanListView,
    ExpenseDetailView,
    ExpenseListCreateView,
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
        "expenses/",
        ExpenseListCreateView.as_view(),
        name="expense-list-create",
    ),

    path(
        "expenses/<uuid:pk>/",
        ExpenseDetailView.as_view(),
        name="expense-detail",
    ),
]