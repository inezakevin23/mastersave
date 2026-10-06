from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Payment, Payout, PayoutDestination
from .mode import is_demo_mode
from .payout_services import mark_payout_failed, mark_payout_successful


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
	actions = ["demo_mark_successful", "demo_mark_failed"]
	actions_on_top = True
	actions_on_bottom = True

	def get_readonly_fields(self, request, obj=None):
		readonly = list(super().get_readonly_fields(request, obj))
		if obj is not None and is_demo_mode():
			readonly.remove("status")
		return readonly

	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == "status" and is_demo_mode():
			kwargs["choices"] = [
				(Payout.Status.REQUESTED, "Requested"),
				(Payout.Status.PROCESSING, "Processing"),
				(Payout.Status.SUCCESSFUL, "Demo: Successful"),
				(Payout.Status.FAILED, "Demo: Failed"),
			]
		return super().formfield_for_choice_field(
			db_field,
			request,
			**kwargs,
		)

	def save_model(self, request, obj, form, change):
		if change and is_demo_mode():
			current = self.get_object(request, obj.pk)
			previous_status = current.status
			target_status = obj.status
			if target_status != previous_status:
				if previous_status not in {
					Payout.Status.REQUESTED,
					Payout.Status.PROCESSING,
				}:
					raise ValidationError(
						"Only requested or processing payouts can be demo-finalized."
					)
				if target_status == Payout.Status.SUCCESSFUL:
					self.demo_mark_successful(
						request,
						Payout.objects.filter(pk=obj.pk),
					)
				elif target_status == Payout.Status.FAILED:
					self.demo_mark_failed(
						request,
						Payout.objects.filter(pk=obj.pk),
					)
				else:
					raise ValidationError(
						"Demo status can only be set to successful or failed."
					)
				obj.refresh_from_db()
				return
		super().save_model(request, obj, form, change)

	def get_actions(self, request):
		actions = super().get_actions(request)
		if not is_demo_mode():
			actions.pop("demo_mark_successful", None)
			actions.pop("demo_mark_failed", None)
		return actions

	@admin.action(description="Demo: mark selected payouts successful")
	def demo_mark_successful(self, request, queryset):
		if not is_demo_mode():
			self.message_user(
				request,
				"Demo payout controls are disabled outside test mode.",
				level=messages.ERROR,
			)
			return

		updated = 0
		for payout in queryset.select_related(
			"allowance_release",
			"savings_bucket",
		):
			if payout.status not in {
				Payout.Status.REQUESTED,
				Payout.Status.PROCESSING,
			}:
				continue

			demo_reference = f"DEMO-{payout.reference}"
			try:
				mark_payout_successful(
					payout=payout,
					verified_data={
						"status": "SUCCESSFUL",
						"currency": payout.currency,
						"reference": payout.reference,
						"amount": str(payout.amount),
					},
				)
			except ValidationError as exc:
				self.message_user(
					request,
					f"Payout {payout.reference} was not finalized: {exc}",
					level=messages.ERROR,
				)
				continue

			payout.refresh_from_db()
			payout.provider_status = "DEMO_SUCCESSFUL"
			payout.provider_reference = demo_reference
			payout.raw_response = {
				"demo": True,
				"status": "SUCCESSFUL",
				"reference": demo_reference,
				"amount": str(payout.amount),
				"currency": payout.currency,
			}
			payout.save(
				update_fields=[
					"provider_status",
					"provider_reference",
					"raw_response",
					"updated_at",
				]
			)

			if payout.allowance_release_id:
				release = payout.allowance_release
				release.provider = "demo"
				release.provider_reference = demo_reference
				release.save(
					update_fields=[
						"provider",
						"provider_reference",
						"updated_at",
					]
				)
			if payout.savings_transaction_id:
				savings_transaction = payout.savings_transaction
				savings_transaction.description = "Demo savings withdrawal payout"
				savings_transaction.save(update_fields=["description"])
			updated += 1

		self.message_user(
			request,
			f"Simulated success for {updated} payout(s). No funds were sent.",
			level=messages.SUCCESS,
		)

	@admin.action(description="Demo: mark selected payouts failed")
	def demo_mark_failed(self, request, queryset):
		if not is_demo_mode():
			self.message_user(
				request,
				"Demo payout controls are disabled outside test mode.",
				level=messages.ERROR,
			)
			return

		updated = 0
		for payout in queryset:
			if payout.status not in {
				Payout.Status.REQUESTED,
				Payout.Status.PROCESSING,
			}:
				continue
			try:
				mark_payout_failed(
					payout=payout,
					reason="Simulated demo failure; no funds were sent.",
				)
			except ValidationError as exc:
				self.message_user(
					request,
					f"Payout {payout.reference} was not updated: {exc}",
					level=messages.ERROR,
				)
				continue
			updated += 1

		self.message_user(
			request,
			f"Simulated failure for {updated} payout(s). No funds were sent.",
			level=messages.SUCCESS,
		)


