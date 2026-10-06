import os

import requests


class FlutterwaveError(Exception):
    pass


class FlutterwaveTransportError(FlutterwaveError):
    pass


class FlutterwaveClient:
    def __init__(self):
        self.secret_key = (
            os.getenv("FLUTTERWAVE_SECRET_KEY")
            or os.getenv("FLW_SECRET_KEY")
        )
        self.public_key = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
        self.mode = os.getenv(
            "FLUTTERWAVE_MODE",
            os.getenv("FLW_MODE", "test"),
        ).strip().lower()
        base_url = (
            os.getenv("FLUTTERWAVE_BASE_URL")
            or os.getenv("FLW_BASE_URL")
            or "https://api.flutterwave.com"
        ).rstrip("/")
        self.base_url = (
            base_url if base_url.endswith("/v3") else f"{base_url}/v3"
        )
        self.redirect_url = os.getenv("FLUTTERWAVE_REDIRECT_URL", "")

        if not self.secret_key:
            raise FlutterwaveError(
                "FLW_SECRET_KEY is not configured."
            )

        if self.mode not in {"test", "live"}:
            raise FlutterwaveError(
                "FLW_MODE must be either 'test' or 'live'."
            )

        is_test_key = self.secret_key.startswith("FLWSECK_TEST-")
        if self.mode == "test" and not is_test_key:
            raise FlutterwaveError(
                "Test mode requires an FLWSECK_TEST- secret key."
            )
        if self.mode == "live" and is_test_key:
            raise FlutterwaveError(
                "Live mode cannot use an FLWSECK_TEST- secret key."
            )

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method, path, **kwargs):
        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self.headers,
                timeout=30,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise FlutterwaveTransportError(
                "Unable to reach Flutterwave."
            ) from exc

        try:
            data = response.json()
        except ValueError:
            data = {
                "status": "error",
                "message": response.text,
            }

        if not response.ok:
            message = (
                data.get("message", "Flutterwave request failed.")
                if isinstance(data, dict)
                else "Flutterwave request failed."
            )
            raise FlutterwaveError(str(message))

        if not isinstance(data, dict):
            raise FlutterwaveError(
                "Flutterwave returned an invalid response."
            )

        return data

    def charge_rwanda_mobile_money(
        self,
        *,
        amount,
        email,
        phone_number,
        fullname,
        tx_ref,
        order_id,
    ):
        if not self.redirect_url:
            raise FlutterwaveError(
                "FLUTTERWAVE_REDIRECT_URL must be set to a public HTTPS "
                "payment-return URL."
            )

        payload = {
            "amount": int(amount),
            "currency": "RWF",
            "email": email,
            "tx_ref": tx_ref,
            "order_id": order_id,
            "phone_number": phone_number,
            "fullname": fullname,
        }
        if self.redirect_url:
            payload["redirect_url"] = self.redirect_url

        return self._request(
            "POST",
            "/charges?type=mobile_money_rwanda",
            json=payload,
        )

    def verify_transaction(self, transaction_id):
        return self._request(
            "GET",
            f"/transactions/{transaction_id}/verify",
        )

    def create_transfer(
        self,
        *,
        destination,
        amount,
        reference,
        narration,
    ):
        payload = {
            "amount": int(amount),
            "currency": "RWF",
            "debit_currency": "RWF",
            "beneficiary_name": destination.beneficiary_name,
            "reference": reference,
            "narration": narration,
        }

        if destination.method == destination.Method.MOBILE_MONEY:
            payload.update(
                {
                    "account_bank": destination.network,
                    "account_number": destination.phone_number,
                }
            )
        elif destination.method == destination.Method.BANK:
            payload.update(
                {
                    "account_bank": destination.bank_code,
                    "account_number": destination.account_number,
                    "destination_branch_code": destination.branch_code,
                }
            )
        else:
            raise FlutterwaveError("Unsupported payout method.")

        return self._request(
            "POST",
            "/transfers",
            json=payload,
        )

    def verify_transfer(self, transfer_id):
        return self._request(
            "GET",
            f"/transfers/{transfer_id}",
        )