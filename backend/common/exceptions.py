from django.core.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework.views import exception_handler


def mastersave_exception_handler(
    exc,
    context,
):
    if isinstance(exc, ValidationError):
        data = (
            exc.message_dict
            if hasattr(exc, "message_dict")
            else {
                "detail": exc.messages
            }
        )

        return Response(
            {
                "success": False,
                "error": data,
            },
            status=400,
        )

    return exception_handler(
        exc,
        context,
    )