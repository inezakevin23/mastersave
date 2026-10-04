from django.urls import path

from .views import (
    AllocationDetailView,
    AllocationListCreateView,
)


urlpatterns = [
    path(
        "",
        AllocationListCreateView.as_view(),
        name="allocation-list-create",
    ),

    path(
        "<uuid:pk>/",
        AllocationDetailView.as_view(),
        name="allocation-detail",
    ),
]