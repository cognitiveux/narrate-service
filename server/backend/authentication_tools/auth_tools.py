from django.conf import settings
from backend.serializers import RefreshTokenSerializer
from backend.views_utils import request_details
from backend.custom_logging import logger as log
import jwt


def authenticate(request):
    try:
        log.debug("[auth_tools.authenticate] - {} - {}".format(request.path, request_details(request)))
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return False, None

        data = {
            "refresh": refresh_token
        }

        _, new_token = RefreshTokenSerializer(data).validate(data)
        access_token = new_token.get("resource_str")
        payload = jwt.decode(
            access_token,
            settings.SIMPLE_JWT["SIGNING_KEY"],
            settings.SIMPLE_JWT["ALGORITHM"],
            audience=settings.SIMPLE_JWT["AUDIENCE"]
        )
        return True, payload
    except Exception as e:
        return False, None


def auth_required(view_func):
    def wrap(request, *args, **kwargs):
        is_valid, payload = authenticate(request)
        return view_func(request, is_valid, payload, **kwargs)

    return wrap
