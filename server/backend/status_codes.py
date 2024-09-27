from rest_framework import serializers
from drf_yasg import openapi
from .custom_logging import logger as log
from .models import *


RESOURCE_NAMES = {
	"jwt": "JSON Web Token",
	"user": "User",
	"c_reset_task_id": "Celery task ID for reset code",
	"ecclesiastical_treasure": "Ecclesiastical Treasure",
	"media_file": "Media File",
	"password": "Password",
	"reset_code": "Reset code",
	"expired_reset_code": "Expired reset code",
	"incorrect_reset_code": "Incorrect reset code",
	"not_requested_reset_code": "Not requested reset code",
}

RESPONSE_TYPES = {
	"bool": "\<Boolean\>",
	"float": "\<Float\>",
	"int": "\<Integer\>",
	"dict": "\<Dictionary\>",
	"array": "\<Array\>",
}

IGNORE_BAD_REQUEST = ["SystemLogsList",]

STATUS_CODES = {
	"resource_is_activated": {
		"code": 200,
		"msg": "Success. Also returns whether {} is activated or not in `resource_is_activated`."
	},
	"success": {
		"code": 200,
		"msg": "Success"
	},
	"success_with_status_return": {
		"code": 200,
		"msg": "Success. The status is returned in `task_status`."
	},
	"resource_created_return_obj": {
		"code": 201,
		"msg": "{} has been created successfully. The value is returned in `resource_obj`."
	},
	"resource_created_return_str": {
		"code": 201,
		"msg": "{} has been created successfully. The value is returned in `resource_str`."
	},
	"bad_formatted_json": {
		"code": 400,
		"msg": "Json parse failed"
	},
	"bad_request": {
		"code": 400,
		"msg": "Bad request (Invalid data) - Any missing, already existing or bad formatted fields will be returned"
	},
	"unauthorized": {
		"code": 401,
		"msg": "Unauthorized - The request lacks valid authentication credentials."
	},
	"resource_not_activated": {
		"code": 403,
		"msg": "Forbidden. {} is not activated. You must activate it to proceed."
	},
	"resource_not_allowed": {
		"code": 403,
		"msg": "Forbidden. You are not allowed to access this resource."
	},
	"resource_not_found": {
		"code": 404,
		"msg": "{} not found"
	},
	"method_not_allowed": {
		"code": 405,
		"msg": "Method not allowed"
	},
	"unsupported_media_type": {
		"code": 415,
		"msg": "Unsupported media type"
	},
	"resource_expired": {
		"code": 422,
		"msg": "{} has expired"
	},
	"resource_incorrect": {
		"code": 422,
		"msg": "{} is incorrect"
	},
	"resource_not_requested": {
		"code": 422,
		"msg": "{} not requested"
	},
	"internal_server_error": {
		"code": 500,
		"msg": "Internal server error"
	},
}

VARIABLE_RESULTS = {
	"request_limit_exceeded": {
		"code": 422,
		"msg": "Request limit exceeded. Try again in %s minutes.",
		"type": [RESPONSE_TYPES["int"]],
	}
}

GENERAL_DESCRIPTIONS = {
	"already_exists_fields": "Any field that is unique and already exists, will be returned in the list",
	"bad_formatted_fields": "Any field that is not in the correct format will be returned in the list",
	"email": "The email of the individual",
	"error_details": "A dictionary that contains descriptive information " \
		"about the validation errors in the form of key-value pairs. " \
		"Each key is a string that corresponds to the problematic field " \
		"and the associated value is a list of strings that contains the error details. " \
		"If a JSON parse error occurred, there will be only one key named `json`.",
	"message": "A general message description",
	"missing_required_fields": "The missing required fields are returned as a list",
	"name": "The name of the individual",
	"extra_details": "Extra details regarding the resource",
	"resource": "A value associated with that resource",
	"resource_array": "An array with all the available data",
	"resource_is_activated": "True if resource is activated, False otherwise",
	"resource_name": "The name of the resource",
	"resource_obj": "A dictionary that contains the JWT " \
		"in the form of key-value pairs. " \
		"The key `access` is a string that corresponds to the JWT access token " \
		"and the key `refresh` is a string that corresponds to the JWT refresh token. ",
	"resource_str": "A string value associated with the resource_name",
	"surname": "The surname of the individual",
	"task_status": "The status of the task: ['PENDING', 'SUCCESS', 'FAILURE']",
	"reason": "The reason behind this error message",
}

CUSTOM_RESPONSES = {}

FIELD_TYPES = {
	"already_exists_fields": openapi.TYPE_ARRAY,
	"bad_formatted_fields": openapi.TYPE_ARRAY,
	"error_details": openapi.TYPE_OBJECT,
	"extra_details": openapi.TYPE_STRING,
	"message": openapi.TYPE_STRING,
	"missing_required_fields": openapi.TYPE_ARRAY,
	"resource": openapi.TYPE_STRING,
	"resource_array": openapi.TYPE_ARRAY,
	"resource_is_activated": openapi.TYPE_BOOLEAN,
	"resource_name": openapi.TYPE_STRING,
	"resource_obj": openapi.TYPE_OBJECT,
	"resource_str": openapi.TYPE_STRING,
	"task_status": openapi.TYPE_STRING,
	"reason": openapi.TYPE_STRING,
}

ENUM_VARIABLES = {
	"ActivateAccount": {},
	"Login": {},
	"PollResetEmailStatus": {
		"resource_name": ["c_reset_task_id", "user"],
	},
	"RefreshToken": {},
	"RegisterUser": {},
	"RequestPasswordResetCode": {},
	"ResetAccountPassword": {
		"reason": [
			"expired_reset_code",
			"incorrect_reset_code",
			"not_requested_reset_code",
		]
	},
	"UpdatePassword": {},
	"UpdateProfile": {},
	"EcclesiasticalTreasuresCreate": {},
	"EcclesiasticalTreasuresDelete": {},
	"EcclesiasticalTreasuresFetch": {},
	"EcclesiasticalTreasuresList": {},
	"EcclesiasticalTreasuresMediaDelete": {
		"resource_name": ["ecclesiastical_treasure", "media_file"],
	},
	"EcclesiasticalTreasuresMediaList": {},
	"EcclesiasticalTreasuresMediaUpdate": {
		"resource_name": ["ecclesiastical_treasure", "media_file"],
	},
	"EcclesiasticalTreasuresMediaUploadNew": {
		"resource_name": ["ecclesiastical_treasure", "media_file"],
	},
	"EcclesiasticalTreasuresUpdate": {},
	"FileMgmtMediaTempAdd": {},
	"FileMgmtMediaTempDelete": {},
	"SystemLogsList": {},
}

VIEWS_DESCRIPTION = {
	"ActivateAccount": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_name",
				"resource_is_activated",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [415, 500],
			"variables": [
				"message",
			]
		},
	],
	"Login": [
		{
			"status_code": [201],
			"variables": [
				"message",
				"resource_name",
				"resource_obj",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details",
			]
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
		{
			"status_code": [403, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
	],
	 "PollResetEmailStatus": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"task_status"
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [415, 500],
			"variables": [
				"message",
			]
		},
	],
	"RefreshToken": [
		{
			"status_code": [201],
			"variables": [
				"message",
				"resource_name",
				"resource_str"
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"error_details"
			]
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"RegisterUser": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_name"
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [415, 500],
			"variables": [
				"message",
			]
		},
	],
	"RequestPasswordResetCode": [
		{
			"status_code": [200, 404, 422],
			"variables": [
				"message",
				"resource_name"
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [415, 500],
			"variables": [
				"message",
			]
		},
	],
	"ResetAccountPassword": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [422],
			"variables": [
				"message",
				"resource_name",
				"reason"
			]
		},
		{
			"status_code": [415, 500],
			"variables": [
				"message",
			]
		},
	],
	"UpdatePassword": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
		{
			"status_code": [422],
			"variables": [
				"message",
				"resource_name",
			]
		},
	],
	"UpdateProfile": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresCreate": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresDelete": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresFetch": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_obj",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
		{
			"status_code": [404],
			"variables": [
				"message",
				"resource_name",
			]
		},
	],
	"EcclesiasticalTreasuresList": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_array",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresMediaDelete": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresMediaList": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_array",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 415, 500],
			"variables": [
				"message",
			]
		},
		{
			"status_code": [404],
			"variables": [
				"message",
				"resource_name",
			]
		},
	],
	"EcclesiasticalTreasuresMediaUpdate": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresMediaUploadNew": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"EcclesiasticalTreasuresUpdate": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
	"FileMgmtMediaTempAdd": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_obj",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [405],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [401, 500],
			"variables": [
				"message",
			]
		},
	],
	"FileMgmtMediaTempDelete": [
		{
			"status_code": [200, 404],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [400],
			"variables": [
				"message",
				"bad_formatted_fields",
				"missing_required_fields",
				"already_exists_fields",
				"error_details"
			],
		},
		{
			"status_code": [405],
			"variables": [
				"message",
				"resource_name",
			]
		},
		{
			"status_code": [401, 500],
			"variables": [
				"message",
			]
		},
	],
	"SystemLogsList": [
		{
			"status_code": [200],
			"variables": [
				"message",
				"resource_array",
			]
		},
		{
			"status_code": [401, 403, 415, 500],
			"variables": [
				"message",
			]
		},
	],
}

def _wrong_method_schema():
	message_key = "message"
	schema_dict = {
		"type": openapi.TYPE_OBJECT,
		"title": "Response body for status code 405",
		"description": "Following keys are returned as json",
		"properties": {
			message_key: {
				"type": FIELD_TYPES[message_key],
				"description": GENERAL_DESCRIPTIONS[message_key],
			},
		}
	}
	return openapi.Schema(**schema_dict)


def _bad_request_schema():
	missing_required_fields = "missing_required_fields"
	already_exist_fields = "already_exist_fields"
	bad_formatted_fields = "bad_formatted_fields"
	error_details = "error_details"
	message_key = "message"
	schema_dict = {
		"type": openapi.TYPE_OBJECT,
		"title": "Response body for status code 400",
		"description": "Following keys are returned as json",
		"properties": {
			already_exist_fields: {
				"type": FIELD_TYPES[already_exist_fields],
				"description": GENERAL_DESCRIPTIONS[already_exist_fields],
				"items": {
					"type": openapi.TYPE_STRING
				}
			},
			bad_formatted_fields: {
				"type": FIELD_TYPES[bad_formatted_fields],
				"description": GENERAL_DESCRIPTIONS[bad_formatted_fields],
				"items": {
					"type": openapi.TYPE_STRING
				}
			},
			missing_required_fields: {
				"type": FIELD_TYPES[missing_required_fields],
				"description": GENERAL_DESCRIPTIONS[missing_required_fields],
				"items": {
					"type": openapi.TYPE_STRING
				}
			},
			error_details: {
				"type": FIELD_TYPES[error_details],
				"description": GENERAL_DESCRIPTIONS[error_details],
				"items": {
					"type": openapi.TYPE_STRING
				}
			},
			message_key: {
				"type": FIELD_TYPES[message_key],
				"description": GENERAL_DESCRIPTIONS[message_key],
			},
		}
	}
	return openapi.Schema(**schema_dict)


def build_response_dictionary(status_list, is_description=True):
	response_dict = {}

	for status_item in status_list:
		code, msg = get_code_and_response(status_item, is_description)
		if code in response_dict.keys():
			response_dict[code] += " or " + msg
		else:
			response_dict[code] = msg

	return response_dict


def get_code_and_response(status_item,is_description=False):
	code = ""
	msg = ""

	if status_item[0] in STATUS_CODES.keys():
		if len(status_item)==1:
			msg = STATUS_CODES[status_item[0]]["msg"]
		elif len(status_item)==2:
			msg = STATUS_CODES[status_item[0]]["msg"].format(RESOURCE_NAMES[status_item[1]])
		elif len(status_item)==3:
			msg = STATUS_CODES[status_item[0]]["msg"].format(RESOURCE_NAMES[status_item[1]],RESPONSE_TYPES[status_item[2]])
		code = STATUS_CODES[status_item[0]]["code"]
	elif status_item[0] in VARIABLE_RESULTS.keys():
		if is_description:
			type_list = VARIABLE_RESULTS[status_item[0]]["type"]
			msg = VARIABLE_RESULTS[status_item[0]]["msg"]%(tuple(type_list))
		else:
			msg = VARIABLE_RESULTS[status_item[0]]["msg"]%(tuple(status_item[1:]))
		code = VARIABLE_RESULTS[status_item[0]]["code"]
	return code,msg


def build_fields(classname, status_keys):
	status_text = build_response_dictionary(status_keys)
	response_dict = {}
	field_dict = {}

	for response_body in VIEWS_DESCRIPTION[classname]:
		property_dict = {}
		for variable_name in response_body["variables"]:
			property_dict[variable_name] = {
				"type": FIELD_TYPES[variable_name],
				"description": GENERAL_DESCRIPTIONS[variable_name]
			}
			if variable_name in ENUM_VARIABLES[classname]:
				property_dict[variable_name]["enum"] = ENUM_VARIABLES[classname][variable_name]
			if FIELD_TYPES[variable_name]==openapi.TYPE_ARRAY:
				property_dict[variable_name]["items"] = {
					"type": openapi.TYPE_STRING
				}

		schema_dict = {
			"type": openapi.TYPE_OBJECT,
			"description": "Following keys are returned as json"
		}

		for status_code in response_body["status_code"]:
			schema_dict["title"] = "Response body for status code {}".format(status_code)

			if classname in CUSTOM_RESPONSES and status_code in CUSTOM_RESPONSES[classname]:
				schema_dict = CUSTOM_RESPONSES[classname][status_code]
			else:
				schema_dict["properties"] = property_dict

			response_dict[status_code] = openapi.Response(
				description=status_text[status_code],
				schema=openapi.Schema(**schema_dict)
			)

	response_dict[405] = openapi.Response(status_text[405],_wrong_method_schema())

	if classname not in IGNORE_BAD_REQUEST:
		if 400 not in response_dict:
			response_dict[400] = openapi.Response(status_text[400],_bad_request_schema())

	for status_code in status_text.keys():
		if not status_code in response_dict.keys():
			response_dict[status_code]=status_text[status_code]

	return response_dict
