import os

from django.conf import settings


def is_demo_mode():
    mode = os.getenv(
        "FLUTTERWAVE_MODE",
        os.getenv("FLW_MODE", "test"),
    ).strip().lower()
    return settings.DEBUG and mode == "test"