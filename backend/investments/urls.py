from django.urls import path

from .views import (
    InvestmentAccountDetailView,
    InvestmentAccountListView,
    InvestmentProductDetailView,
    InvestmentProductListView,
    InvestmentRequestDetailView,
    InvestmentRequestListCreateView,
    InvestmentTransactionListView,
    GrowSummaryView,
)


urlpatterns = [
    path(
        "products/",
        InvestmentProductListView.as_view(),
        name="investment-product-list",
    ),

    path(
        "products/<uuid:pk>/",
        InvestmentProductDetailView.as_view(),
        name="investment-product-detail",
    ),

    path(
        "requests/",
        InvestmentRequestListCreateView.as_view(),
        name="investment-request-list-create",
    ),

    path(
        "requests/<uuid:pk>/",
        InvestmentRequestDetailView.as_view(),
        name="investment-request-detail",
    ),

    path(
        "accounts/",
        InvestmentAccountListView.as_view(),
        name="investment-account-list",
    ),

    path(
        "accounts/<uuid:pk>/",
        InvestmentAccountDetailView.as_view(),
        name="investment-account-detail",
    ),

    path(
        "transactions/",
        InvestmentTransactionListView.as_view(),
        name="investment-transaction-list",
    ),
    path(
        "summary/grow/",
        GrowSummaryView.as_view(),
        name="investment-summary-grow",
    ),
]