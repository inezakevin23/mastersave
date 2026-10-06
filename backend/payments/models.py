import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Payment(models.Model):

	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		PROCESSING = "PROCESSING", "Processing"
		SUCCESSFUL = "SUCCESSFUL", "Successful"
		FAILED = "FAILED", "Failed"
		REVERSED = "REVERSED", "Reversed"

	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)

	scholar = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="payments",
	)

	reference = models.CharField(
		max_length=100,
		unique=True,
	)

	order_id = models.CharField(
		max_length=100,
		unique=True,
	)

	amount = models.DecimalField(
		max_digits=14,
		decimal_places=0,
		validators=[MinValueValidator(1)],
	)

	currency = models.CharField(
		max_length=3,
		default="RWF",
	)

	payment_method = models.CharField(
		max_length=50,
		default="mobilemoneyrw",
	)

	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.PENDING,
	)

	flutterwave_transaction_id = models.BigIntegerField(
		null=True,
		blank=True,
	)

	flutterwave_reference = models.CharField(
		max_length=255,
		blank=True,
	)

	authorization_url = models.URLField(
		blank=True,
	)

	deposit = models.OneToOneField(
		"deposits.Deposit",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="payment",
	)

	raw_response = models.JSONField(
		default=dict,
		blank=True,
	)

	completed_at = models.DateTimeField(
		null=True,
		blank=True,
	)

	created_at = models.DateTimeField(
		auto_now_add=True,
	)

	updated_at = models.DateTimeField(
		auto_now=True,
	)

	class Meta:
		ordering = ["-created_at"]

	def clean(self):
		super().clean()

		if self.deposit_id and self.scholar_id:
			if self.deposit.scholar_id != self.scholar_id:
				raise ValidationError(
					{"deposit": "Deposit must belong to this scholar."}
				)

			if self.deposit.amount != self.amount:
				raise ValidationError(
					{"deposit": "Deposit amount must match the payment."}
				)

			if self.deposit.currency != self.currency:
				raise ValidationError(
					{"deposit": "Deposit currency must match the payment."}
				)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.reference} - {self.amount} {self.currency}"


class PayoutDestination(models.Model):

	class Method(models.TextChoices):
		MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
		BANK = "BANK", "Bank Account"

	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)

	scholar = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="payout_destinations",
	)

	method = models.CharField(
		max_length=20,
		choices=Method.choices,
	)

	beneficiary_name = models.CharField(
		max_length=255,
	)

	network = models.CharField(
		max_length=30,
		blank=True,
	)

	phone_number = models.CharField(
		max_length=30,
		blank=True,
	)

	bank_code = models.CharField(
		max_length=50,
		blank=True,
	)

	branch_code = models.CharField(
		max_length=50,
		blank=True,
	)

	account_number = models.CharField(
		max_length=100,
		blank=True,
	)

	currency = models.CharField(
		max_length=3,
		default="RWF",
	)

	is_default = models.BooleanField(
		default=False,
	)

	created_at = models.DateTimeField(
		auto_now_add=True,
	)

	updated_at = models.DateTimeField(
		auto_now=True,
	)

	def clean(self):
		super().clean()

		if self.method == self.Method.MOBILE_MONEY:
			errors = {}
			if not self.network:
				errors["network"] = "Mobile money network is required."
			if not self.phone_number:
				errors["phone_number"] = "Mobile money phone number is required."
			if errors:
				raise ValidationError(errors)

		elif self.method == self.Method.BANK:
			required = {
				"bank_code": self.bank_code,
				"branch_code": self.branch_code,
				"account_number": self.account_number,
			}
			missing = {
				field: f"{field} is required."
				for field, value in required.items()
				if not value
			}
			if missing:
				raise ValidationError(missing)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		if self.method == self.Method.MOBILE_MONEY:
			masked_phone = f"***{self.phone_number[-4:]}"
			return f"{self.beneficiary_name} - {self.network} - {masked_phone}"

		masked_account = f"***{self.account_number[-4:]}"
		return f"{self.beneficiary_name} - {masked_account}"


class Payout(models.Model):

	class Kind(models.TextChoices):
		ALLOWANCE = "ALLOWANCE", "Allowance"
		SAVINGS_WITHDRAWAL = "SAVINGS_WITHDRAWAL", "Savings Withdrawal"
		INVESTMENT_WITHDRAWAL = (
			"INVESTMENT_WITHDRAWAL",
			"Investment Withdrawal",
		)

	class Status(models.TextChoices):
		REQUESTED = "REQUESTED", "Requested"
		PROCESSING = "PROCESSING", "Processing"
		SUCCESSFUL = "SUCCESSFUL", "Successful"
		FAILED = "FAILED", "Failed"
		CANCELLED = "CANCELLED", "Cancelled"

	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)

	scholar = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="payouts",
	)

	kind = models.CharField(
		max_length=30,
		choices=Kind.choices,
	)

	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.REQUESTED,
	)

	amount = models.DecimalField(
		max_digits=14,
		decimal_places=0,
		validators=[MinValueValidator(1)],
	)

	currency = models.CharField(
		max_length=3,
		default="RWF",
	)

	reference = models.CharField(
		max_length=100,
		unique=True,
	)

	destination = models.ForeignKey(
		PayoutDestination,
		on_delete=models.PROTECT,
		related_name="payouts",
	)

	allowance_release = models.OneToOneField(
		"spend.AllowanceRelease",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="payout",
	)

	savings_bucket = models.ForeignKey(
		"savings.SavingsBucket",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="withdrawal_payouts",
	)

	savings_transaction = models.OneToOneField(
		"savings.SavingsTransaction",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="payout",
	)

	investment_account = models.ForeignKey(
		"investments.InvestmentAccount",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="withdrawal_payouts",
	)

	flutterwave_transfer_id = models.BigIntegerField(
		null=True,
		blank=True,
	)

	provider_reference = models.CharField(
		max_length=255,
		blank=True,
	)

	provider_status = models.CharField(
		max_length=50,
		blank=True,
	)

	fee = models.DecimalField(
		max_digits=14,
		decimal_places=0,
		null=True,
		blank=True,
	)

	failure_reason = models.TextField(
		blank=True,
	)

	raw_response = models.JSONField(
		default=dict,
		blank=True,
	)

	initiated_at = models.DateTimeField(
		null=True,
		blank=True,
	)

	completed_at = models.DateTimeField(
		null=True,
		blank=True,
	)

	created_at = models.DateTimeField(
		auto_now_add=True,
	)

	updated_at = models.DateTimeField(
		auto_now=True,
	)

	class Meta:
		ordering = ["-created_at"]

	def clean(self):
		super().clean()

		sources = [
			self.allowance_release_id,
			self.savings_bucket_id,
			self.investment_account_id,
		]
		if sum(source is not None for source in sources) != 1:
			raise ValidationError(
				{"source": "Payout must have exactly one source."}
			)

		required_source = {
			self.Kind.ALLOWANCE: self.allowance_release_id,
			self.Kind.SAVINGS_WITHDRAWAL: self.savings_bucket_id,
			self.Kind.INVESTMENT_WITHDRAWAL: self.investment_account_id,
		}.get(self.kind)
		if required_source is None:
			raise ValidationError(
				{"source": "Payout source does not match its kind."}
			)

		if self.destination_id and self.scholar_id:
			if self.destination.scholar_id != self.scholar_id:
				raise ValidationError(
					{"destination": "Destination must belong to this scholar."}
				)
			if self.destination.currency != self.currency:
				raise ValidationError(
					{"destination": "Destination currency must match the payout."}
				)

		if self.allowance_release_id and self.scholar_id:
			if self.allowance_release.plan.scholar_id != self.scholar_id:
				raise ValidationError(
					{"allowance_release": "Release must belong to this scholar."}
				)

		if self.savings_bucket_id and self.scholar_id:
			if self.savings_bucket.scholar_id != self.scholar_id:
				raise ValidationError(
					{"savings_bucket": "Savings bucket must belong to this scholar."}
				)

		if self.investment_account_id and self.scholar_id:
			if self.investment_account.scholar_id != self.scholar_id:
				raise ValidationError(
					{"investment_account": "Investment account must belong to this scholar."}
				)

		if self.savings_transaction_id:
			if self.savings_transaction.bucket_id != self.savings_bucket_id:
				raise ValidationError(
					{"savings_transaction": "Transaction must belong to the payout bucket."}
				)
			if self.savings_transaction.bucket.scholar_id != self.scholar_id:
				raise ValidationError(
					{"savings_transaction": "Transaction must belong to this scholar."}
				)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.reference} - {self.amount} {self.currency}"


