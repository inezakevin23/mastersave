from django.urls import path

from .views import (
    PaymentInitiateView,
    PayoutDetailView,
    PayoutDestinationListCreateView,
    PayoutListView,
    WithdrawalView,
    flutterwave_redirect,
)


urlpatterns = [
    path(
        "flutterwave/redirect/",
        flutterwave_redirect,
        name="flutterwave-redirect",
    ),
    path(
        "deposit/mobile-money/",
        PaymentInitiateView.as_view(),
        name="deposit-mobile-money",
    ),
    path(
        "payout-destinations/",
        PayoutDestinationListCreateView.as_view(),
        name="payout-destinations",
    ),
    path(
        "withdrawals/",
        WithdrawalView.as_view(),
        name="withdrawal-create",
    ),
    path(
        "payouts/",
        PayoutListView.as_view(),
        name="payout-list",
    ),
    path(
        "payouts/<uuid:pk>/",
        PayoutDetailView.as_view(),
        name="payout-detail",
    ),
]