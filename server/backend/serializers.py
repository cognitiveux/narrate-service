from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.urls import (
	resolve,
	Resolver404
)
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from six import text_type
from drf_yasg import openapi
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
	TokenObtainPairSerializer,
	TokenRefreshSerializer,
)

import datetime

from .application_error import ApplicationError
from .custom_logging import logger as log
from .models import *
from .status_codes import get_code_and_response
from .views_utils import generate_random_uuid


ALREADY_EXISTS_FIELDS = "already_exists_fields"
BAD_FORMATTED_FIELDS = "bad_formatted_fields"
ERROR_DETAILS = "error_details"
MESSAGE = "message"
MISSING_REQUIRED_FIELDS = "missing_required_fields"
UNIQUE = "unique"
DJANGO_VALIDATION_ERROR_CODES = [
	"invalid",
	"invalid_choice",
	"min_length",
	"min_value",
	"max_length",
	"max_value",
]


class CustomSerializer(serializers.ModelSerializer):
	def formatted_error_response(self, include_already_exists=False):
		error_details_dict = {}
		response = {
			ALREADY_EXISTS_FIELDS: [],
			BAD_FORMATTED_FIELDS: [],
			MISSING_REQUIRED_FIELDS: []
		}
		append_bad_request_msg = False

		for field in self._errors:
			if not isinstance(self._errors[field][0], list):
				if self._errors[field][0].code == UNIQUE:
					response[ALREADY_EXISTS_FIELDS].append(field)

				elif self._errors[field][0].code in DJANGO_VALIDATION_ERROR_CODES:
					response[BAD_FORMATTED_FIELDS].append(field)
				else:
					response[MISSING_REQUIRED_FIELDS].append(field)

			error_details_dict[field] = []

			for item in self._errors[field]:
				error_details_dict[field].append(item)

		if not include_already_exists:
			response.pop(ALREADY_EXISTS_FIELDS)

		response[ERROR_DETAILS] = error_details_dict

		return response


class LoginSerializer(TokenObtainPairSerializer):
	def __init__(self, *args, **kwargs):
		super(LoginSerializer, self).__init__(*args, **kwargs)
		self.fields["organization"] = serializers.ChoiceField(
			label="Organization",
			required=True,
			choices=OrganizationModel.ORGANIZATION_CHOICES
		)

	@classmethod
	def get_token(cls, user):
		token = super(LoginSerializer, cls).get_token(user)
		email = user.email
		user_row = Users.objects.filter(email=email).values("role", "organization", "name", "surname")
		user_row_role = user_row[0].get("role")
		user_row_organization = user_row[0].get("organization")
		user_row_name = user_row[0].get("name")
		user_row_surname = user_row[0].get("surname")

		token["iss"] = "NarrateAuthentication"
		token["iat"] = int(str(datetime.datetime.now().timestamp()).split(".")[0])
		token["sub"] = email
		token["organization"] = user_row_organization
		token["name"] = user_row_name
		token["role"] = user_row_role
		token["session_id"] = generate_random_uuid()
		token["surname"] = user_row_surname

		return token

	def validate(self, attrs):
		user = None
		self.response_body = {}
		bad_formatted_fields = []
		missing_required_fields = []
		already_exists_fields = []
		error_details_dict = {}

		for field_name in self.fields:
			try:
				self.fields[field_name].run_validation(attrs.get(field_name))
			except serializers.ValidationError as e:
				if e.detail[0].code == "blank" or e.detail[0].code == "null":
					missing_required_fields.append(field_name)
				else:
					bad_formatted_fields.append(field_name)

				if field_name not in error_details_dict:
					error_details_dict[field_name] = []

				error_details_dict[field_name].append(e.__repr__())

		if len(bad_formatted_fields) > 0 or len(missing_required_fields) > 0:
			log.debug("[LoginSerializer] [validate] Bad formatted fields")
			self.response_body[MISSING_REQUIRED_FIELDS] = missing_required_fields
			self.response_body[BAD_FORMATTED_FIELDS] = bad_formatted_fields
			self.response_body[ALREADY_EXISTS_FIELDS] = already_exists_fields
			self.response_body[ERROR_DETAILS] = error_details_dict
			status, message = get_code_and_response(["bad_request"])
			self.response_body[MESSAGE] = message
			return status, self.response_body

		email = attrs.get("email")
		password = attrs.get("password")
		organization = attrs.get("organization")

		next_url = attrs.get("next_url", "")
		is_allowed_host = False

		if next_url:
			try:
				is_allowed_host = url_has_allowed_host_and_scheme(next_url, None)
				url = iri_to_uri(next_url)
				base_url_no_params = url.split("?")[0]
				resolved_url = resolve(base_url_no_params)
			except Resolver404 as e:
				log.debug("[LoginSerializer] [validate] Can't resolve next_url: {}. Reason: {}".format(
						next_url,
						str(e)
					)
				)
				is_allowed_host = False
			except Exception as e:
				log.debug("[LoginSerializer] [validate] Error in checking next_url: {}. Reason: {}".format(
						next_url,
						str(e)
					)
				)
				is_allowed_host = False

		if not is_allowed_host:
			next_url = "/backend/dashboard/"

		user_row = Users.objects.filter(email=email, organization=organization).first()

		if not user_row:
			log.debug("[LoginSerializer] [validate] User not found")
			raise ApplicationError(["resource_not_found", "user"])

		user_fk_id = user_row.id
		active_user_row = ActiveUsers.objects.filter(user_fk_id=user_fk_id).first()

		if not active_user_row:
			raise ApplicationError(["resource_not_activated", "user"])

		if not active_user_row.ts_activation:
			raise ApplicationError(["resource_not_activated", "user"])

		if user_row.check_password(password):
			log.debug("[LoginSerializer] [validate] Valid credentials")
			refresh = self.get_token(user_row)
			status_code, message = get_code_and_response(["resource_created_return_obj", "jwt"])
			self.response_body[MESSAGE] = message
			self.response_body["resource_name"] = "jwt"
			tokens = {
				"access": text_type(refresh.access_token),
				"refresh": text_type(refresh)
			}
			self.response_body["resource_obj"] = tokens
			self.response_body["next_url"] = next_url
			return status_code, self.response_body
		else:
			log.debug("[LoginSerializer] [validate] Invalid credentials")
			raise ApplicationError(["unauthorized"])

	def formatted_error_response(self):
		return self.response_body


class RefreshTokenSerializer(TokenRefreshSerializer):
	def validate(self, attrs):
		self.response_body = {}

		try:
			token = super(RefreshTokenSerializer, self).validate(attrs)
			status_code, message = get_code_and_response(["resource_created_return_str", "jwt"])
			self.response_body[MESSAGE] = message
			self.response_body["resource_name"] = "jwt"
			self.response_body["resource_str"] = text_type(token.get("access"))
			return status_code, self.response_body
		except Exception as e:
			log.debug("[RefreshTokenSerializer] Error occurred during validation of JWT: {}".format(str(e)))
			raise ApplicationError(["unauthorized"])


class RegisterUserSerializer(CustomSerializer):

	class Meta:
		model = Users
		fields = ("email", "name", "organization",
				  "password", "surname")
		extra_kwargs = {
			"email": {
				"required": True
			},
			"name": {
				"required": True
			},
			"organization": {
				"required": True
			},
			"password": {
				"required": True
			},
			"surname": {
				"required": True
			},
		}


class EcclesiasticalTreasuresCreateSerializer(CustomSerializer):
	title_en = serializers.CharField(required=True)
	title_gr = serializers.CharField(required=False, allow_blank=True)
	title_bg = serializers.CharField(required=False, allow_blank=True)
	title_tk = serializers.CharField(required=False, allow_blank=True)
	appellation_en = serializers.CharField(required=True)
	appellation_gr = serializers.CharField(required=False, allow_blank=True)
	appellation_bg = serializers.CharField(required=False, allow_blank=True)
	appellation_tk = serializers.CharField(required=False, allow_blank=True)
	existing_obj_code = serializers.CharField(required=False, allow_blank=True)
	desc_short_version = serializers.CharField(required=False, allow_blank=True)
	desc_extended_version = serializers.CharField(required=False, max_length=10000, allow_blank=True)
	time_span = serializers.CharField(required=False, allow_blank=True)
	kind = serializers.CharField(required=False, allow_blank=True)
	creator = serializers.CharField(required=False, allow_blank=True)
	beginning_of_existence = serializers.CharField(required=False, allow_blank=True)
	was_in_church = serializers.BooleanField(required=False, default=False)
	was_in_another_country = serializers.BooleanField(required=False, default=False)
	was_lost_and_found = serializers.BooleanField(required=False, default=False)
	dimension = serializers.CharField(required=False, allow_blank=True)
	material = serializers.CharField(required=False, allow_blank=True)
	inscription = serializers.CharField(required=False, allow_blank=True)
	manuscript_text = serializers.CharField(required=False, allow_blank=True)
	event_information = serializers.CharField(required=False, allow_blank=True)
	previous_documentation = serializers.CharField(required=False, allow_blank=True)
	relevant_bibliography = serializers.CharField(required=False, allow_blank=True)
	preservation_status = serializers.CharField(required=False, allow_blank=True)
	conservation_status = serializers.CharField(required=False, allow_blank=True)
	group_of_objects = serializers.ListField(
		required=False,
		child=serializers.CharField(required=False, allow_blank=True),
		allow_empty=True,
		min_length=None,
		max_length=None
	)
	collection_it_belongs = serializers.CharField(required=False, allow_blank=True)
	position_of_treasure = serializers.CharField(required=False, allow_blank=True)
	people_that_help_with_documentation = serializers.ListField(
		required=False,
		child=serializers.CharField(required=False, allow_blank=True),
		allow_empty=True,
		min_length=None,
		max_length=None
	)

	class Meta:
		model = Ecclesiastical_Treasures
		fields = ("title_en", "title_gr", "title_bg", "title_tk",
			"appellation_en", "appellation_gr", "appellation_bg", "appellation_tk",
			"existing_obj_code", "desc_short_version", "desc_extended_version", "time_span", "kind", "creator",
			"beginning_of_existence", "was_in_church", "was_in_another_country", "was_lost_and_found", "dimension", "material",
			"inscription", "manuscript_text", "event_information", "previous_documentation", "relevant_bibliography",
			"preservation_status", "conservation_status", "group_of_objects", "collection_it_belongs",
			"position_of_treasure", "people_that_help_with_documentation",
		)
		extra_kwargs = {
			"title_en": {
				"required": True
			},
			"title_gr": {
				"required": False,
				"allow_blank": True
			},
			"title_bg": {
				"required": False,
				"allow_blank": True
			},
			"title_tk": {
				"required": False,
				"allow_blank": True
			},
			"appellation_en": {
				"required": True
			},
			"appellation_gr": {
				"required": False,
				"allow_blank": True
			},
			"appellation_bg": {
				"required": False,
				"allow_blank": True
			},
			"appellation_tk": {
				"required": False,
				"allow_blank": True
			},
			"existing_obj_code": {
				"required": False,
				"allow_blank": True
			},
			"desc_short_version": {
				"required": False,
				"allow_blank": True
			},
			"desc_extended_version": {
				"required": False,
				"allow_blank": True
			},
			"time_span": {
				"required": False,
				"allow_blank": True
			},
			"kind": {
				"required": False,
				"allow_blank": True
			},
			"creator": {
				"required": False,
				"allow_blank": True
			},
			"beginning_of_existence": {
				"required": False,
				"allow_blank": True
			},
			"was_in_church": {
				"required": False,
				"allow_blank": True
			},
			"was_in_another_country": {
				"required": False,
				"allow_blank": True
			},
			"was_lost_and_found": {
				"required": False,
				"allow_blank": True
			},
			"dimension": {
				"required": False,
				"allow_blank": True
			},
			"material": {
				"required": False,
				"allow_blank": True
			},
			"inscription": {
				"required": False,
				"allow_blank": True
			},
			"manuscript_text": {
				"required": False,
				"allow_blank": True
			},
			"event_information": {
				"required": False,
				"allow_blank": True
			},
			"previous_documentation": {
				"required": False,
				"allow_blank": True
			},
			"relevant_bibliography": {
				"required": False,
				"allow_blank": True
			},
			"preservation_status": {
				"required": False,
				"allow_blank": True
			},
			"conservation_status": {
				"required": False,
				"allow_blank": True
			},
			"group_of_objects": {
				"required": False,
				"allow_blank": True
			},
			"collection_it_belongs": {
				"required": False,
				"allow_blank": True
			},
			"position_of_treasure": {
				"required": False,
				"allow_blank": True
			},
			"people_that_help_with_documentation": {
				"required": False,
				"allow_blank": True
			},
		}


class EcclesiasticalTreasuresUpdateSerializer(CustomSerializer):
	uuid = serializers.CharField(required=True)
	title_en = serializers.CharField(required=True)
	title_gr = serializers.CharField(required=False, allow_blank=True)
	title_bg = serializers.CharField(required=False, allow_blank=True)
	title_tk = serializers.CharField(required=False, allow_blank=True)
	appellation_en = serializers.CharField(required=True)
	appellation_gr = serializers.CharField(required=False, allow_blank=True)
	appellation_bg = serializers.CharField(required=False, allow_blank=True)
	appellation_tk = serializers.CharField(required=False, allow_blank=True)
	existing_obj_code = serializers.CharField(required=False, allow_blank=True)
	desc_short_version = serializers.CharField(required=False, allow_blank=True)
	desc_extended_version = serializers.CharField(required=False, max_length=10000, allow_blank=True)
	time_span = serializers.CharField(required=False, allow_blank=True)
	kind = serializers.CharField(required=False, allow_blank=True)
	creator = serializers.CharField(required=False, allow_blank=True)
	beginning_of_existence = serializers.CharField(required=False, allow_blank=True)
	was_in_church = serializers.BooleanField(required=False, default=False)
	was_in_another_country = serializers.BooleanField(required=False, default=False)
	was_lost_and_found = serializers.BooleanField(required=False, default=False)
	dimension = serializers.CharField(required=False, allow_blank=True)
	material = serializers.CharField(required=False, allow_blank=True)
	inscription = serializers.CharField(required=False, allow_blank=True)
	manuscript_text = serializers.CharField(required=False, allow_blank=True)
	event_information = serializers.CharField(required=False, allow_blank=True)
	previous_documentation = serializers.CharField(required=False, allow_blank=True)
	relevant_bibliography = serializers.CharField(required=False, allow_blank=True)
	preservation_status = serializers.CharField(required=False, allow_blank=True)
	conservation_status = serializers.CharField(required=False, allow_blank=True)
	group_of_objects = serializers.ListField(
		required=False,
		child=serializers.CharField(required=False, allow_blank=True),
		allow_empty=True,
		min_length=None,
		max_length=None
	)
	collection_it_belongs = serializers.CharField(required=False, allow_blank=True)
	position_of_treasure = serializers.CharField(required=False, allow_blank=True)
	people_that_help_with_documentation = serializers.ListField(
		required=False,
		child=serializers.CharField(required=False, allow_blank=True),
		allow_empty=True,
		min_length=None,
		max_length=None
	)

	class Meta:
		model = Ecclesiastical_Treasures
		fields = ("uuid", "title_en", "title_gr", "title_bg", "title_tk",
			"appellation_en", "appellation_gr", "appellation_bg", "appellation_tk",
			"existing_obj_code", "desc_short_version", "desc_extended_version", "time_span", "kind", "creator",
			"beginning_of_existence", "was_in_church", "was_in_another_country", "was_lost_and_found", "dimension", "material",
			"inscription", "manuscript_text", "event_information", "previous_documentation", "relevant_bibliography",
			"preservation_status", "conservation_status", "group_of_objects", "collection_it_belongs",
			"position_of_treasure", "people_that_help_with_documentation",
		)
		extra_kwargs = {
			"uuid": {
				"required": True
			},
			"title_en": {
				"required": True
			},
			"title_gr": {
				"required": False,
				"allow_blank": True
			},
			"title_bg": {
				"required": False,
				"allow_blank": True
			},
			"title_tk": {
				"required": False,
				"allow_blank": True
			},
			"appellation_en": {
				"required": True
			},
			"appellation_gr": {
				"required": False,
				"allow_blank": True
			},
			"appellation_bg": {
				"required": False,
				"allow_blank": True
			},
			"appellation_tk": {
				"required": False,
				"allow_blank": True
			},
			"existing_obj_code": {
				"required": False,
				"allow_blank": True
			},
			"desc_short_version": {
				"required": False,
				"allow_blank": True
			},
			"desc_extended_version": {
				"required": False,
				"allow_blank": True
			},
			"time_span": {
				"required": False,
				"allow_blank": True
			},
			"kind": {
				"required": False,
				"allow_blank": True
			},
			"creator": {
				"required": False,
				"allow_blank": True
			},
			"beginning_of_existence": {
				"required": False,
				"allow_blank": True
			},
			"was_in_church": {
				"required": False,
				"allow_blank": True
			},
			"was_in_another_country": {
				"required": False,
				"allow_blank": True
			},
			"was_lost_and_found": {
				"required": False,
				"allow_blank": True
			},
			"dimension": {
				"required": False,
				"allow_blank": True
			},
			"material": {
				"required": False,
				"allow_blank": True
			},
			"inscription": {
				"required": False,
				"allow_blank": True
			},
			"manuscript_text": {
				"required": False,
				"allow_blank": True
			},
			"event_information": {
				"required": False,
				"allow_blank": True
			},
			"previous_documentation": {
				"required": False,
				"allow_blank": True
			},
			"relevant_bibliography": {
				"required": False,
				"allow_blank": True
			},
			"preservation_status": {
				"required": False,
				"allow_blank": True
			},
			"conservation_status": {
				"required": False,
				"allow_blank": True
			},
			"group_of_objects": {
				"required": False,
				"allow_blank": True
			},
			"collection_it_belongs": {
				"required": False,
				"allow_blank": True
			},
			"position_of_treasure": {
				"required": False,
				"allow_blank": True
			},
			"people_that_help_with_documentation": {
				"required": False,
				"allow_blank": True
			},
		}


class EcclesiasticalTreasuresListSerializer(CustomSerializer):
	search_keyword = serializers.CharField(required=False)
	exact_match = serializers.BooleanField(required=False)

	class Meta:
		model = Ecclesiastical_Treasures
		fields= ("search_keyword", "exact_match",)
		extra_kwargs = {}


class EcclesiasticalTreasuresMediaListSerializer(CustomSerializer):
	treasure_id = serializers.CharField(required=True)

	class Meta:
		model = Ecclesiastical_Treasures
		fields= ("treasure_id",)
		extra_kwargs = {}


class EcclesiasticalTreasuresMediaDeleteSerializer(CustomSerializer):
	treasure_id = serializers.CharField(required=True)
	media_id = serializers.CharField(required=True)

	class Meta:
		model = Ecclesiastical_Treasures
		fields= ("treasure_id", "media_id")
		extra_kwargs = {}


class EcclesiasticalTreasuresMediaUpdateSerializer(CustomSerializer):
	class Meta:
		model = Ecclesiastical_Treasures
		fields= ()
		extra_kwargs = {}
		swagger_schema_fields = {
			"type": openapi.TYPE_OBJECT,
			"title": "The details of the ecclesiastical treasure media you would like to update",
			"properties": {
				"updating_data": openapi.Schema(
					title="Details for updating media of ecclesiastical treasures",
					type=openapi.TYPE_OBJECT,
					properties={
						"treasure_id": openapi.Schema(
							title="The uuid of the ecclesiastical treasure",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
						"old_media_id": openapi.Schema(
							title="The uuid of the old media",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
						"new_media_id": openapi.Schema(
							title="The uuid of the new media",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
					}
				),
			}
		}


class EcclesiasticalTreasuresMediaUploadNewSerializer(CustomSerializer):
	class Meta:
		model = Ecclesiastical_Treasures
		fields= ()
		extra_kwargs = {}
		swagger_schema_fields = {
			"type": openapi.TYPE_OBJECT,
			"title": "The details of the ecclesiastical treasure media you would like to upload",
			"properties": {
				"uploading_data": openapi.Schema(
					title="Details for uploading new media for the ecclesiastical treasures",
					type=openapi.TYPE_OBJECT,
					properties={
						"treasure_id": openapi.Schema(
							title="The uuid of the ecclesiastical treasure",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
						"media_type_id": openapi.Schema(
							title="The type ID of the new media",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
						"type": openapi.Schema(
							title="The type of the new media",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
					}
				),
			}
		}


class EcclesiasticalTreasuresFetchSerializer(CustomSerializer):
	treasure_id = serializers.CharField(required=True)

	class Meta:
		model = Ecclesiastical_Treasures
		fields= ("treasure_id",)
		extra_kwargs = {}


class EcclesiasticalTreasuresDeleteSerializer(CustomSerializer):
	treasure_id = serializers.CharField(required=True)

	class Meta:
		model = Ecclesiastical_Treasures
		fields= ("treasure_id",)
		extra_kwargs = {}


class TempMediaAddSerializer(CustomSerializer):
	class Meta:
		model = MediaFile
		fields= ("file_src", "uuid", "file_ext",)
		extra_kwargs = {
			"file_src": {
				"required": False
			},
			"file_ext": {
				"required": False
			},
			"uuid": {
				"required": False
			},
		}


class UpdateProfileSerializer(CustomSerializer):
	class Meta:
		model = MediaFile
		fields= ()
		extra_kwargs = {}
		swagger_schema_fields = {
			"type": openapi.TYPE_OBJECT,
			"title": "The details of the user profile you would like to update",
			"properties": {
				"updating_data": openapi.Schema(
					title="Details for updating the user profile",
					type=openapi.TYPE_OBJECT,
					properties={
						"name": openapi.Schema(
							title="User's Name",
							type=openapi.TYPE_STRING,
							maxLength=500,
						),
						"surname": openapi.Schema(
							title="User's Surname",
							type=openapi.TYPE_STRING,
							maxLength=500,
						),
						"telephone": openapi.Schema(
							title="User's Telephone",
							type=openapi.TYPE_STRING,
							maxLength=100,
						),
						"media_type_id": openapi.Schema(
							title="New Media Type ID",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
						"type": openapi.Schema(
							title="New Media Type",
							type=openapi.TYPE_STRING,
							maxLength=1000,
						),
					}
				),
			}
		}


class UpdatePasswordSerializer(CustomSerializer):
	current_password = serializers.CharField(max_length=500, source="Users.password")
	new_password = serializers.CharField(max_length=500, source="Users.password")

	class Meta:
		model = Users
		fields = ("current_password", "new_password")
		extra_kwargs = {
			"current_password": {
				"required": True
			},
			"new_password": {
				"required": True
			}
		}


class RequestPasswordResetCodeSerializer(CustomSerializer):
	email = serializers.EmailField(max_length=100, source="Users.email")

	class Meta:
		model = Users
		fields = ("email",)
		extra_kwargs = {
			"email": {
				"required": True
			},
		}


class PollResetEmailStatusSerializer(CustomSerializer):
	email = serializers.EmailField(max_length=100, source="Users.email")

	class Meta:
		model = Users
		fields = ("email",)
		extra_kwargs = {
			"email": {
				"required": True
			},
		}


class ResetPasswordSerializer(CustomSerializer):
	email = serializers.EmailField(max_length=100, source="Users.email")
	password = serializers.CharField(max_length=500, source="Users.password")

	class Meta:
		model = ResetPassword
		fields = ("email", "password", "reset_code",)
		extra_kwargs = {
			"email": {
				"required": True
			},
			"password": {
				"required": True
			},
			"reset_code": {
				"required": True
			}
		}


class ActivateAccountSerializer(CustomSerializer):
	email = serializers.EmailField(max_length=100, source="Users.email")

	class Meta:
		model = ActiveUsers
		fields = ("email", "activation_code")
		extra_kwargs = {
			"email": {
				"required": True
			},
			"activation_code": {
				"required": True
			}
		}
