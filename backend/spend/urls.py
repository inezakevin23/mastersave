from django.urls import path

from .views import (
    AllowancePlanDetailView,
    AllowancePlanListCreateView,
    ExpenseDetailView,
    ExpenseListCreateView,
)


urlpatterns = [
    path(
        "plans/",
        AllowancePlanListCreateView.as_view(),
        name="allowance-plan-list-create",
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