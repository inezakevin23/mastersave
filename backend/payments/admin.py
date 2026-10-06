from django.contrib import admin

from .models import Payment, Payout, PayoutDestination


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = [
		"reference",
		"scholar",
		"amount",
		"currency",
		"status",
		"created_at",
	]
	list_filter = ["status", "currency", "payment_method"]
	search_fields = ["reference", "order_id", "scholar__email"]
	readonly_fields = [field.name for field in Payment._meta.fields]


@admin.register(PayoutDestination)
class PayoutDestinationAdmin(admin.ModelAdmin):
	list_display = [
		"beneficiary_name",
		"scholar",
		"method",
		"currency",
		"is_default",
	]
	list_filter = ["method", "currency", "is_default"]
	search_fields = ["beneficiary_name", "scholar__email"]


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
	list_display = [
		"reference",
		"scholar",
		"kind",
		"amount",
		"currency",
		"status",
		"created_at",
	]
	list_filter = ["kind", "status", "currency"]
	search_fields = ["reference", "scholar__email"]
	readonly_fields = [field.name for field in Payout._meta.fields]


