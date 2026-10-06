from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError

from .services import (
    approve_investment_request,
    complete_investment_request,
    reject_investment_request,
)

from .models import (
    InvestmentAccount,
    InvestmentProduct,
    InvestmentRequest,
    InvestmentTransaction,
)


@admin.register(InvestmentProduct)
class InvestmentProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "partner_name",
        "minimum_amount",
        "annual_rate",
        "term_months",
        "risk_level",
        "status",
    ]

    list_filter = [
        "status",
        "risk_level",
    ]

    search_fields = [
        "name",
        "partner_name",
    ]


@admin.register(InvestmentRequest)
class InvestmentRequestAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "scholar",
        "product",
        "amount",
        "status",
        "requested_at",
        "completed_at",
    ]

    list_filter = [
        "status",
        "product",
    ]

    search_fields = [
        "reference",
        "scholar__email",
        "scholar__first_name",
        "scholar__last_name",
    ]

    readonly_fields = [
        "reference",
        "status",
        "requested_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]

    @admin.action(
        description="Approve selected requests"
    )
    def approve_requests(
        self,
        request,
        queryset,
    ):
        approved = 0

        for investment_request in queryset:
            try:
                approve_investment_request(
                    investment_request
                )
                approved += 1
            except ValidationError as exc:
                self.message_user(
                    request,
                    str(exc),
                    level=messages.ERROR,
                )

        if approved:
            self.message_user(
                request,
                f"{approved} investment request(s) approved.",
                level=messages.SUCCESS,
            )

    @admin.action(
        description="Reject selected requests"
    )
    def reject_requests(
        self,
        request,
        queryset,
    ):
        rejected = 0

        for investment_request in queryset:
            try:
                reject_investment_request(
                    investment_request
                )
                rejected += 1
            except ValidationError as exc:
                self.message_user(
                    request,
                    str(exc),
                    level=messages.ERROR,
                )

        if rejected:
            self.message_user(
                request,
                f"{rejected} investment request(s) rejected.",
                level=messages.SUCCESS,
            )

    @admin.action(
        description="Complete selected approved requests"
    )
    def complete_requests(
        self,
        request,
        queryset,
    ):
        completed = 0

        for investment_request in queryset:
            try:
                complete_investment_request(
                    investment_request
                )
                completed += 1
            except ValidationError as exc:
                self.message_user(
                    request,
                    str(exc),
                    level=messages.ERROR,
                )

        if completed:
            self.message_user(
                request,
                f"{completed} investment request(s) completed.",
                level=messages.SUCCESS,
            )

    actions = [
        approve_requests,
        reject_requests,
        complete_requests,
    ]


class InvestmentTransactionInline(
    admin.TabularInline
):
    model = InvestmentTransaction
    extra = 0

    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
    ]


@admin.register(InvestmentAccount)
class InvestmentAccountAdmin(admin.ModelAdmin):
    list_display = [
        "scholar",
        "product",
        "balance_display",
        "status",
        "maturity_date",
    ]

    list_filter = [
        "status",
        "product",
    ]

    search_fields = [
        "scholar__email",
        "scholar__first_name",
        "scholar__last_name",
        "partner_account_reference",
    ]

    inlines = [
        InvestmentTransactionInline,
    ]

    def balance_display(self, obj):
        return obj.balance

    balance_display.short_description = "Balance"


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "account",
        "transaction_type",
        "amount",
        "status",
        "occurred_at",
    ]

    list_filter = [
        "transaction_type",
        "status",
    ]

    search_fields = [
        "reference",
        "account__scholar__email",
    ]

    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
    ]
