from django.urls import path

from .views import (
    SavingsBucketDetailView,
    SavingsBucketListCreateView,
    SavingsContributionView,
    SavingsTransactionListView,
    SavingsWithdrawalView,
)


urlpatterns = [
    path(
        "buckets/",
        SavingsBucketListCreateView.as_view(),
        name="savings-bucket-list-create",
    ),

    path(
        "buckets/<uuid:pk>/",
        SavingsBucketDetailView.as_view(),
        name="savings-bucket-detail",
    ),

    path(
        "buckets/<uuid:pk>/contribute/",
        SavingsContributionView.as_view(),
        name="savings-contribute",
    ),

    path(
        "buckets/<uuid:pk>/withdraw/",
        SavingsWithdrawalView.as_view(),
        name="savings-withdraw",
    ),

    path(
        "transactions/",
        SavingsTransactionListView.as_view(),
        name="savings-transactions",
    ),
]