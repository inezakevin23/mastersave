from django.http import JsonResponse
from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .flutterwave import FlutterwaveError, FlutterwaveTransportError
from .models import Payment, Payout, PayoutDestination
from .payment_services import (
	initiate_mobile_money_deposit,
	verify_and_finalize_payment,
)
from .payout_services import send_payout_to_flutterwave
from .serializers import (
	PaymentInitiateSerializer,
	PaymentSerializer,
	PayoutDestinationSerializer,
	PayoutSerializer,
	WithdrawalSerializer,
)


def flutterwave_redirect(request):
	if request.method != "GET":
		return JsonResponse(
			{"detail": "Method not allowed."},
			status=405,
		)

	transaction_id = request.GET.get("transaction_id")
	reference = request.GET.get("tx_ref")
	if not transaction_id or not reference:
		return JsonResponse(
			{"success": False, "detail": "Missing transaction_id or tx_ref."},
			status=400,
		)

	payment = Payment.objects.filter(reference=reference).first()
	if payment is None:
		return JsonResponse(
			{"success": False, "detail": "Payment was not found."},
			status=404,
		)

	try:
		deposit = verify_and_finalize_payment(
			payment=payment,
			flutterwave_transaction_id=transaction_id,
		)
	except FlutterwaveTransportError:
		return JsonResponse(
			{
				"success": False,
				"detail": "Could not verify payment with Flutterwave yet.",
			},
			status=502,
		)
	except (FlutterwaveError, ValidationError):
		return JsonResponse(
			{"success": False, "detail": "Flutterwave did not confirm this payment."},
			status=400,
		)

	return JsonResponse(
		{
			"success": True,
			"reference": payment.reference,
			"deposit_id": str(deposit.id),
		},
		status=200,
	)


class PaymentInitiateView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		serializer = PaymentInitiateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			payment = initiate_mobile_money_deposit(
				scholar=request.user,
				amount=serializer.validated_data["amount"],
			)
		except FlutterwaveError as exc:
			return Response(
				{"success": False, "detail": str(exc)},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		return Response(
			{
				"success": True,
				"data": PaymentSerializer(payment).data,
			},
			status=status.HTTP_201_CREATED,
		)


class PayoutDestinationListCreateView(
	generics.ListCreateAPIView
):
	permission_classes = [IsAuthenticated]
	serializer_class = PayoutDestinationSerializer

	def get_queryset(self):
		return (
			PayoutDestination.objects
			.filter(scholar=self.request.user)
			.order_by("-is_default", "-created_at")
		)

	def perform_create(self, serializer):
		serializer.save(scholar=self.request.user)


class WithdrawalView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		serializer = WithdrawalSerializer(
			data=request.data,
			context={"request": request},
		)
		serializer.is_valid(raise_exception=True)
		payout = serializer.save()

		try:
			payout = send_payout_to_flutterwave(payout)
		except FlutterwaveTransportError:
			payout.refresh_from_db()
			return Response(
				{
					"success": True,
					"data": PayoutSerializer(payout).data,
				},
				status=status.HTTP_202_ACCEPTED,
			)
		except FlutterwaveError as exc:
			payout.refresh_from_db()
			return Response(
				{
					"success": False,
					"detail": str(exc),
					"data": PayoutSerializer(payout).data,
				},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		return Response(
			{
				"success": True,
				"data": PayoutSerializer(payout).data,
			},
			status=status.HTTP_202_ACCEPTED,
		)


class PayoutListView(generics.ListAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = PayoutSerializer

	def get_queryset(self):
		return (
			Payout.objects
			.filter(scholar=self.request.user)
			.select_related(
				"destination",
				"savings_bucket",
				"allowance_release",
			)
		)


class PayoutDetailView(generics.RetrieveAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = PayoutSerializer

	def get_queryset(self):
		return (
			Payout.objects
			.filter(scholar=self.request.user)
			.select_related(
				"destination",
				"savings_bucket",
				"allowance_release",
			)
		)

# Create your views here.
