from rest_framework.exceptions import *
from rest_framework.views import exception_handler
from backend.status_codes import get_code_and_response
from .application_error import ApplicationError
from rest_framework.response import Response

def custom_exception_handler(exc, context):
	response = exception_handler(exc, context)
	if isinstance(exc, ApplicationError):
		return Response(data=exc.get_response_body(), status=exc.status_code)
	elif isinstance(exc, MethodNotAllowed):
		response.data["message"]=get_code_and_response(["method_not_allowed"])[1]
		response.data.pop("detail", None)
	elif isinstance(exc, AuthenticationFailed):
		response.data["message"] = get_code_and_response(["unauthorized"])[1]
		response.data.pop("detail", None)
		response.data.pop("messages", None)
		response.data.pop("code", None)
	elif isinstance(exc, NotAuthenticated):
		response.data["message"] = get_code_and_response(["unauthorized"])[1]
		response.data.pop("detail", None)
		response.data.pop("messages", None)
	elif isinstance(exc, ParseError):
		response.data["message"] = get_code_and_response(["bad_formatted_json"])[1]
		response.data["bad_formatted_fields"] = []
		response.data["missing_required_fields"] = []
		response.data.pop("detail", None)
	elif isinstance(exc, UnsupportedMediaType):
		response.data["message"] = get_code_and_response(["unsupported_media_type"])[1]
		response.data.pop("detail", None)

	return response
