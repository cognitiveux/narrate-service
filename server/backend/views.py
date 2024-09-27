from celery.result import AsyncResult
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.signing import (
	BadSignature,
	SignatureExpired,
	TimestampSigner
)
from django.db import transaction
from django.http import (
	HttpResponse,
	HttpResponseForbidden,
	HttpResponseRedirect,
)
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.static import serve
from drf_yasg.utils import swagger_auto_schema
from PIL import Image
from rest_framework import (
	parsers,
	permissions,
	status,
)
from rest_framework.generics import (
	CreateAPIView,
	DestroyAPIView,
	GenericAPIView,
)
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
	TokenObtainPairView,
	TokenRefreshView,
)

from rest_framework_simplejwt.tokens import RefreshToken as SimplejwtRefreshToken

import base64
import hashlib
import pathlib
import shutil
import os
import uuid

from narrate_project.celery import app
from .application_error import ApplicationError

from .custom_logging import logger as log
from .models import *
from .serializers import *
from .status_codes import *
from .views_utils import *
from .authentication_tools import auth_tools as at
from .forms import MediaFileForm
from .password_policy import is_compliant


BAD_REQUEST = "bad_request"
CONTENT = "content"
INTERNAL_SERVER_ERROR = "internal_server_error"
MESSAGE = "message"
RESOURCE = "resource"
RESOURCE_ARRAY = "resource_array"
RESOURCE_IS_ACTIVATED = "resource_is_activated"
RESOURCE_IS_ALREADY_ACTIVATED = "resource_is_already_activated"
RESOURCE_NAME = "resource_name"
RESOURCE_OBJ = "resource_obj"
STATUS_CODE = "status_code"

MAX_CONSERVATION_FILES = 10
MAX_CONTENT_FILES = 10
MAX_MEDIA_FILES = 10
MAX_PHOTOS_FILES = 10
MAX_VIDEOS_FILES = 10

DIR_CODE_MEDIA = "/code/protected_media/"
DIR_MEDIA = "/protected_media/"
DIR_MEDIA_TEMP = "media/temporary/"
DIR_MEDIA_SYNCED = "media/synced/"
TASK_STATUS = "task_status"


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def protected_media(request, is_valid, payload, path):
	if not is_valid:
		return HttpResponseRedirect(reverse("login"))

	return serve(request, path, document_root=settings.PROTECTED_MEDIA_ROOT)


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def loginView(request, is_valid, payload):
	if is_valid:
		return HttpResponseRedirect(reverse("dashboard"))

	template = loader.get_template("backend/authentication/sign_in.html")
	context = {
		"title": "Login",
	}
	return HttpResponse(template.render(context, request))


def logout(request):
	try:
		function_name = "logout"
		function_action = "LOGOUT"
		user_id = None
		req_details = request_details(request)
		log.debug("{} Log out attempt".format(req_details))

		is_valid, payload = at.authenticate(request)

		if not is_valid:
			return HttpResponseRedirect(reverse("login"))

		user_id = payload["user_id"]
		response = HttpResponseRedirect(reverse("login"))
		response.delete_cookie(settings.SIMPLE_JWT["AUTH_REFRESH_COOKIE"], path="/", domain=None, samesite="Strict")
		refresh_token = SimplejwtRefreshToken(request.COOKIES.get("refresh_token"))
		refresh_token.blacklist()
	except Exception as e:
		log.error("{} DB LOG (Internal error): {}".format(req_details, str(e)),
			extra={
				"api": function_name,
				"action": function_action,
				"error_data": str(e),
				"ip_address": get_ip_address(request),
				"is_error": True
			}
		)

	if request.session.get("next_url"):
		del request.session["next_url"]

	log.info("{} DB LOG".format(req_details),
		extra={
			"user_id": user_id,
			"api": function_name,
			"action": function_action,
			"ip_address": get_ip_address(request),
		}
	)
	log.debug("{} SUCCESS".format(req_details))
	return response


def get_user_info(request, user_obj):
	log.debug("{} Will get user's info".format(request_details(request)))
	user = {}

	try:
		user["name"] = user_obj.name
		user["surname"] = user_obj.surname
		user["email"] = user_obj.email
		user["telephone"] = user_obj.telephone or ""
		user["organization"] = user_obj.organization
		user["role"] = user_obj.role
		user["profile_pic_src"] = user_obj.file_src
	except Exception as e:
		user = {
			"name": "",
			"surname": "",
			"email": "",
			"telephone": "",
			"organization": "",
			"role": "",
			"profile_pic_src": "",
		}
		log.debug("{} Error getting user's info. Reason: {}".format(request_details(request), str(e)))

	return user


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signUpView(request):
	template = loader.get_template("backend/authentication/sign_up.html")
	context = {
		"title": "Sign Up",
	}
	return HttpResponse(template.render(context, request))


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def activateAccountView(request):
	template = loader.get_template("backend/authentication/activate_account.html")
	context = {
		"title": "Activate Account",
	}
	return HttpResponse(template.render(context, request))


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forgotPasswordView(request):
	template = loader.get_template("backend/authentication/forgot_password.html")
	context = {
		"title": "Forgot Password",
	}
	return HttpResponse(template.render(context, request))


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def resetPasswordView(request):
	template = loader.get_template("backend/authentication/reset_password.html")
	context = {
		"title": "Reset Password",
	}
	signer = TimestampSigner()
	cuxid_param = request.GET.get("cuxid")

	try:
		if not cuxid_param:
			return HttpResponseForbidden()

		b64_bytes = cuxid_param.encode("ascii")
		cuxid_bytes = base64.b64decode(b64_bytes)
		cuxid_message = cuxid_bytes.decode("ascii")
		unsigned = signer.unsign(cuxid_message, max_age=timedelta(seconds=settings.RESET_PASSWORD_SIGNATURE_MAX_AGE_SEC))
	except SignatureExpired as e:
		log.debug("{} Signature expired: {}".format(request_details(request), str(e)))
		return HttpResponseForbidden()
	except BadSignature as e:
		log.debug("{} Bad Signature: {}".format(request_details(request), str(e)))
		return HttpResponseForbidden()
	except Exception as e:
		log.debug("{} Error occurred: {}".format(request_details(request), str(e)))
		return HttpResponseForbidden()

	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboardView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/dashboard/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/dashboard.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	context = {
		"title": "Dashboard",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"is_editable": True,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def knowledgeRepositoryView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/kr/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/kr.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	context = {
		"title": "Knowledge Repository",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"is_editable": True,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def profileView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/profile/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/profile.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	media_type_uuid = generate_random_uuid()
	context = {
		"title": "My Profile",
		"user_name": user_info.get("name"),
		"user_surname": user_info.get("surname"),
		"user_email": user_info.get("email"),
		"user_telephone": user_info.get("telephone"),
		"user_organization": user_info.get("organization"),
		"user_role": user_info.get("role"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"media_type_uuid": media_type_uuid,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def securityView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/security/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/security.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	context = {
		"title": "Security Settings",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresAddView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/treasures/add/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/treasures/add.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	conservation_photos_uuid = generate_random_uuid()
	content_uuid = generate_random_uuid()
	photos_uuid = generate_random_uuid()
	videos_uuid = generate_random_uuid()
	context = {
		"title": "Add Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"conservation_photos_uuid": conservation_photos_uuid,
		"content_uuid": content_uuid,
		"photos_uuid": photos_uuid,
		"videos_uuid": videos_uuid,
		"max_conservation_media_files": MAX_CONSERVATION_FILES,
		"max_content_media_files": MAX_CONTENT_FILES,
		"max_photos_media_files": MAX_PHOTOS_FILES,
		"max_videos_media_files": MAX_VIDEOS_FILES,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresDeleteView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/delete/?treasure_id=" + treasure_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_obj = Users.objects.filter(id=payload["user_id"]).first()

	if user_obj:
		current_user_id = user_obj.id

		if current_user_id != added_by_user_fk and user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

	user_info = get_user_info(request, user_obj)
	lang_en_row = E56_Language.objects.filter(code="en").first()
	lang_en_fk_id = lang_en_row.id
	title_en_row = E35_Title.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()
	title_en = ""

	if title_en_row:
		title_en = title_en_row.content

	appellation_en_row = E41_Appellation.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()

	appellation_en = ""

	if appellation_en_row:
		appellation_en = appellation_en_row.content

	template = loader.get_template("backend/treasures/delete.html")
	context = {
		"title": "Delete Existing Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"treasure_uuid": treasure_uuid_req,
		"title_en": title_en,
		"appellation_en": appellation_en,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresMediaView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/media/?treasure_id=" + treasure_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_row = Users.objects.filter(
		id=added_by_user_fk
	).first()

	is_editable = False
	if user_row:
		current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
		current_user_id = current_user_obj.id

		if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

		if current_user_id == added_by_user_fk or current_user_obj.role == RoleModel.ADMIN:
			is_editable = True

	template = loader.get_template("backend/treasures/media/list.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	lang_en_row = E56_Language.objects.filter(code="en").first()
	lang_en_fk_id = lang_en_row.id
	title_en_row = E35_Title.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()
	title_en = ""

	if title_en_row:
		title_en = title_en_row.content

	appellation_en_row = E41_Appellation.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()

	appellation_en = ""

	if appellation_en_row:
		appellation_en = appellation_en_row.content

	context = {
		"title": "Manage Media of Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"treasure_uuid": treasure_uuid_req,
		"title_en": title_en,
		"appellation_en": appellation_en,
		"is_editable": is_editable,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresMediaAddView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/media/add/?treasure_id=" + treasure_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_row = Users.objects.filter(
		id=added_by_user_fk
	).first()

	if user_row:
		user_obj = Users.objects.filter(id=payload["user_id"]).first()

		if user_obj.id != added_by_user_fk and user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

	user_info = get_user_info(request, user_obj)
	lang_en_row = E56_Language.objects.filter(code="en").first()
	lang_en_fk_id = lang_en_row.id
	title_en_row = E35_Title.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()
	title_en = ""

	if title_en_row:
		title_en = title_en_row.content

	appellation_en_row = E41_Appellation.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()

	appellation_en = ""

	if appellation_en_row:
		appellation_en = appellation_en_row.content

	template = loader.get_template("backend/treasures/media/upload_new.html")
	media_type_uuid = generate_random_uuid()
	conservation_photos_uuid = generate_random_uuid()
	content_uuid = generate_random_uuid()
	photos_uuid = generate_random_uuid()
	videos_uuid = generate_random_uuid()
	context = {
		"title": "Upload New Media for Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"treasure_uuid": treasure_uuid_req,
		"title_en": title_en,
		"appellation_en": appellation_en,
		"media_type_uuid": media_type_uuid,
		"conservation_photos_uuid": conservation_photos_uuid,
		"content_uuid": content_uuid,
		"photos_uuid": photos_uuid,
		"videos_uuid": videos_uuid,
		"max_media_files": MAX_MEDIA_FILES,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresMediaDeleteView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")
	media_uuid_req = request.GET.get("media_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/media/delete/?treasure_id=" + treasure_uuid_req + "&media_id=" + media_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	media_obj_row = MediaFile.objects.filter(
		uuid = media_uuid_req,
		treasure_fk_id = treasure_uuid_req,
	).first()

	if not media_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_obj = Users.objects.filter(id=payload["user_id"]).first()

	if user_obj:
		current_user_id = user_obj.id

		if current_user_id != added_by_user_fk and user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

	user_info = get_user_info(request, user_obj)
	lang_en_row = E56_Language.objects.filter(code="en").first()
	lang_en_fk_id = lang_en_row.id
	title_en_row = E35_Title.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()
	title_en = ""

	if title_en_row:
		title_en = title_en_row.content

	appellation_en_row = E41_Appellation.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()

	appellation_en = ""

	if appellation_en_row:
		appellation_en = appellation_en_row.content

	template = loader.get_template("backend/treasures/media/delete.html")
	context = {
		"title": "Delete Media of Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"treasure_uuid": treasure_uuid_req,
		"media_uuid": media_uuid_req,
		"media_type": media_obj_row.media_type,
		"title_en": title_en,
		"appellation_en": appellation_en,
		"file_src": "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
											str(media_obj_row.dir_path) + "/" + str(media_obj_row.uuid) + "_resized" + str(media_obj_row.file_ext),
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresMediaUpdateView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")
	media_uuid_req = request.GET.get("media_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/media/update/?treasure_id=" + treasure_uuid_req + "&media_id=" + media_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	media_obj_row = MediaFile.objects.filter(
		uuid = media_uuid_req,
		treasure_fk_id = treasure_uuid_req,
	).first()

	if not media_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_obj = Users.objects.filter(id=payload["user_id"]).first()

	if user_obj:
		current_user_id = user_obj.id

		if current_user_id != added_by_user_fk and user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

	user_info = get_user_info(request, user_obj)
	conservation_photos_uuid = generate_random_uuid()
	lang_en_row = E56_Language.objects.filter(code="en").first()
	lang_en_fk_id = lang_en_row.id
	title_en_row = E35_Title.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()
	title_en = ""

	if title_en_row:
		title_en = title_en_row.content

	appellation_en_row = E41_Appellation.objects.filter(
		treasure_fk_id=treasure_uuid_req,
		language_fk_id=lang_en_fk_id,
	).first()

	appellation_en = ""

	if appellation_en_row:
		appellation_en = appellation_en_row.content

	template = loader.get_template("backend/treasures/media/update.html")
	context = {
		"title": "Update Media of Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"treasure_uuid": treasure_uuid_req,
		"media_uuid": media_uuid_req,
		"media_type": media_obj_row.media_type,
		"media_type_uuid": media_obj_row.media_type_uuid,
		"title_en": title_en,
		"appellation_en": appellation_en,
		"conservation_photos_uuid": conservation_photos_uuid,
		"file_src": "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
											str(media_obj_row.dir_path) + "/" + str(media_obj_row.uuid) + "_resized" + str(media_obj_row.file_ext),
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresUpdateView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/update/?treasure_id=" + treasure_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	added_by_user_fk = treasure_obj_row.user_fk_id
	user_row = Users.objects.filter(
		id=added_by_user_fk
	).first()

	if user_row:
		current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
		current_user_id = current_user_obj.id

		if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
			return HttpResponseRedirect(reverse("no_permission"))

	template = loader.get_template("backend/treasures/update.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	conservation_photos_row = MediaFile.objects.filter(
		media_type = "conservation",
		treasure_fk_id = treasure_uuid_req,
	).first()

	if conservation_photos_row:
		conservation_photos_uuid = conservation_photos_row.media_type_uuid
	else:
		conservation_photos_uuid = generate_random_uuid()

	context = {
		"title": "Update Existing Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
		"conservation_photos_uuid": conservation_photos_uuid,
		"max_conservation_media_files": MAX_CONSERVATION_FILES,
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def treasuresView(request, is_valid, payload):
	treasure_uuid_req = request.GET.get("treasure_id", "")

	if not is_valid:        
		request.session["next_url"] = "/backend/treasures/view/?treasure_id=" + treasure_uuid_req
		return HttpResponseRedirect(reverse("login"))

	treasure_obj_row = Ecclesiastical_Treasures.objects.filter(
		uuid = treasure_uuid_req,
	).first()

	if not treasure_obj_row:
		return HttpResponseRedirect(reverse("dashboard"))

	template = loader.get_template("backend/treasures/view.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	context = {
		"title": "View Existing Ecclesiastical Treasure",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
	}
	return HttpResponse(template.render(context, request))


@at.auth_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def noPermissionView(request, is_valid, payload):
	if not is_valid:
		request.session["next_url"] = "/backend/dashboard/"
		return HttpResponseRedirect(reverse("login"))

	template = loader.get_template("backend/assets_and_tools/no_permission.html")
	user_obj = Users.objects.filter(id=payload["user_id"]).first()
	user_info = get_user_info(request, user_obj)
	context = {
		"title": "No Permission",
		"user_name": user_info.get("name"),
		"user_profile_pic": user_info.get("profile_pic_src"),
	}
	return HttpResponse(template.render(context, request))


class ActivateAccount(GenericAPIView):
	"""
	post:
	Activates the account if the provided activation code matches the latest activation code received via email
	"""
	class_name = "ActivateAccount"
	class_action = "UPDATE"
	serializer_class = ActivateAccountSerializer
	permission_classes = (permissions.AllowAny,)
	response_types = [
		["resource_is_activated", "user"],
		["bad_request"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("ActivateAccount", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request".format(request_details(request)))
		try:
			response = {}
			data = {}
			req_data = request.data
			log.debug("{} START".format(request_details(request)))
			serialized_item = ActivateAccountSerializer(data=req_data)
			is_resource_activated = False
			is_resource_already_activated = False

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					log.debug("{} VALID DATA".format(request_details(request)))
					email = req_data.get("email")
					received_activation_code = req_data.get("activation_code")
					ts_now = now()
					user_row = Users.objects.filter(email=email).values("id")

					if not user_row:
						raise ApplicationError(["resource_not_found", "user"])

					user_fk_id = user_row[0].get("id")
					
					active_user_row = ActiveUsers.objects.filter(
						user_fk_id=user_fk_id
					).values("activation_code", "ts_activation")

					stored_activation_code = active_user_row[0].get("activation_code")
					stored_ts_activation = active_user_row[0].get("ts_activation")

					if stored_activation_code == received_activation_code and not stored_ts_activation:
						log.debug("{} Activation codes match.".format(request_details(request)))
						ActiveUsers.objects.filter(
							user_fk_id=user_fk_id
						).update(
							ts_activation=ts_now
						)
						is_resource_activated = True
					elif stored_ts_activation:
						log.debug("{} Account is already activated {}".format(request_details(request), email))
						is_resource_already_activated = True
					else:
						log.debug("{} Verification codes mismatch.".format(request_details(request)))
						is_resource_activated = False

					log.info("{} DB LOG".format(request_details(request)),
						extra={
							"api": self.class_name,
							"action": self.class_action,
							"data": model_to_json(req_data),
							"ip_address": get_ip_address(request),
						}
					)
					status_code, message = get_code_and_response(["resource_is_activated", "user"])
					content = {}
					content[MESSAGE] = message
					content[RESOURCE_NAME] = "user"
					content[RESOURCE_IS_ACTIVATED] = is_resource_activated
					content[RESOURCE_IS_ALREADY_ACTIVATED] = is_resource_already_activated
					response = {}
					response[CONTENT] = content
					response[STATUS_CODE] = status_code
					log.debug("{} SUCCESS".format(request_details(request)))
					data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to activate account"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class Login(TokenObtainPairView):
	"""
	post:
	Creates a JSON Web Token for login purpose if the provided credentials are correct
	"""
	class_name = "Login"
	class_action = "CREATE"
	serializer_class = LoginSerializer
	permission_classes = (permissions.AllowAny,)
	response_types = [
		["resource_created_return_obj", "jwt"],
		["bad_request"],
		["unauthorized"],
		["resource_not_activated", "user"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("Login", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request".format(request_details(request)))
		data = {}
		response = {}

		try:            
			req_data = request.data
			req_obj = {
				"email": req_data.get("email")
			}
			log.debug("{} START".format(request_details(request)))
			log.debug("{} Requested login email: {}".format(request_details(request), req_data.get("email")))
			status_code, tokens = LoginSerializer(req_data).validate(req_data)
			response[CONTENT] = tokens
			response[STATUS_CODE] = status_code
			log.debug("{} SUCCESS".format(request_details(request)))
			data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
			return Response(data[CONTENT], status=data[STATUS_CODE])
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to login"
			}
			return Response(content, status=status_code)

		log.info("{} DB LOG".format(request_details(request)),
			extra={
				"api": self.class_name,
				"action": self.class_action,
				"data": model_to_json(req_obj),
				"ip_address": get_ip_address(request),
			}
		)
		login_response = Response(data[CONTENT], status=data[STATUS_CODE])
		login_response.set_cookie(
			key = settings.SIMPLE_JWT["AUTH_REFRESH_COOKIE"], 
			value = data["content"]["resource_obj"]["refresh"],
			expires = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
			secure = settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
			httponly = settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
			samesite = settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"]
		)
		return login_response


class PollResetEmailStatus(GenericAPIView):
	"""
	get:
	Polls the status of the reset code ``email``
	"""
	class_name = "PollResetEmailStatus"
	class_action = "LIST"
	serializer_class = PollResetEmailStatusSerializer
	response_types = [
		["success_with_status_return"],
		["bad_request"],
		["resource_not_found", "c_reset_task_id"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("PollResetEmailStatus", response_types)
	email_param = openapi.Parameter(
		"email",
		in_=openapi.IN_QUERY,
		description="Email",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[email_param]
	)
	def get(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}

			req_data = request.GET
			log.debug("{} START".format(request_details(request)))
			serialized_item = PollResetEmailStatusSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				email = req_data.get("email")
				user_row = Users.objects.filter(email=email).values("c_reset_task_id")

				if not user_row:
					raise ApplicationError(["resource_not_found", "user"])

				c_reset_task_id = user_row[0].get("c_reset_task_id")
				result = AsyncResult(c_reset_task_id)

				if not c_reset_task_id or not result:
					raise ApplicationError(["resource_not_found", "c_reset_task_id"])

				c_task_status = "PENDING"

				if result.state == "PENDING":
					c_task_status = "PENDING"
				elif result.state == "FAILURE":
					c_task_status = "FAILURE"
				elif result.state == "SUCCESS":
					c_task_status = "SUCCESS"

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success_with_status_return"])
				content = {}
				content[MESSAGE] = message
				content[TASK_STATUS] = c_task_status
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to poll reset code email status"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class RefreshToken(TokenRefreshView):
	"""
	post:
	Uses the longer-lived refresh token to obtain another access token
	"""
	serializer_class = RefreshTokenSerializer
	permission_classes = (permissions.AllowAny,)
	response_types = [
		["resource_created_return_str", "jwt"],
		["bad_request"],
		["unauthorized"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("RefreshToken", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request".format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data
			status_code, token = RefreshTokenSerializer(req_data).validate(req_data)
			response[CONTENT] = token
			response[STATUS_CODE] = status_code
			log.debug("{} SUCCESS".format(request_details(request)))
			data = response
		except ApplicationError as e:
			log.debug("{} ERROR: {}".format(request_details(request), str(e)))
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.debug("{} Internal error: {}".format(request_details(request), str(e)))
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to refresh token"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class RegisterUser(CreateAPIView):
	"""
	post:
	Creates a new NARRATE user instance
	"""
	class_name = "RegisterUser"
	class_action = "CREATE"
	serializer_class = RegisterUserSerializer
	permission_classes = (permissions.AllowAny,)
	response_types = [
		["success"],
		["bad_request"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("RegisterUser", response_types)

	@app.task(bind=True, time_limit=settings.CELERY_TASK_TIME_LIMIT)
	def send_registration_email_task(self, email, activation_code):
		send_email(email, activation_code)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request".format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data
			req_obj = {
				"email": req_data.get("email"),
				"name": req_data.get("name"),
				"surname": req_data.get("surname"),
				"organization": req_data.get("organization"),
			}
			serialized_user = RegisterUserSerializer(data=req_data)

			if not serialized_user.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_user.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_user.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				email = req_data.get("email")
				name = req_data.get("name")
				surname = req_data.get("surname")
				organization = req_data.get("organization")
				password = req_data.get("password")
				role = RoleModel.REGULAR
				ts_now = now()

				password_hash = make_password(password)

				user = Users(
					email=email,
					name=name,
					organization=organization,
					password=password_hash,
					role=role,
					surname=surname,
					ts_registration=ts_now
				)
				user.save()

				activation_code = generate_random_uuid()
				user_row = Users.objects.filter(email=email).values("id")
				user_fk_id = user_row[0].get("id")

				ActiveUsers.objects.update_or_create(
						user_fk_id=user_fk_id,
						defaults={
							"activation_code": activation_code,
							"frequent_request_count": 1,
							"ts_added": ts_now,
						}
					)

				result = self.send_registration_email_task.apply_async(
					(email, activation_code),
					countdown=settings.EMAIL_COUNTDOWN_SEC
				)
				Users.objects.filter(email=email).update(c_register_task_id=result.id)
				log.debug("{} Will send registration email to: {}. Updating async result with task ID: {}".format(
						request_details(request), email, result.id
					)
				)

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_obj),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "user"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to register user"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class RequestPasswordResetCode(GenericAPIView):
	"""
	post:
	Request a reset code for reset password of account via email
	"""
	class_name = "RequestPasswordResetCode"
	class_action = "CREATE"
	serializer_class = RequestPasswordResetCodeSerializer
	response_types = [
		["success"],
		["bad_request"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["request_limit_exceeded", "user"],
		["internal_server_error"]
	]
	response_dict = build_fields("RequestPasswordResetCode", response_types)

	@app.task(bind=True, time_limit=settings.CELERY_TASK_TIME_LIMIT)
	def send_reset_code_email_task(self, email, reset_code, expiring_reset_password_url):
		send_email(email, reset_code, expiring_reset_password_url)


	@swagger_auto_schema(
		responses=response_dict,
		security=[],
	)
	def post(self, request, *args, **kwargs):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}

			req_data = request.data
			log.debug("{} START".format(request_details(request)))
			serialized_item = RequestPasswordResetCodeSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					log.debug("{} VALID DATA".format(request_details(request)))
					email = req_data.get("email")
					user_row = Users.objects.filter(email=email).values("id")

					if not user_row:
						raise ApplicationError(["resource_not_found", "user"])

					user_fk_id = user_row[0].get("id")
					reset_password_row = ResetPassword.objects.filter(user_fk_id=user_fk_id).first()

					if not reset_password_row:
						new_reset_password_row = ResetPassword(
							user_fk_id=user_fk_id,
							frequent_request_count=0,
							ts_reset=None,
						)
						new_reset_password_row.save()

					reset_password_row = ResetPassword.objects.filter(user_fk_id=user_fk_id).first()
					frequent_request_count = reset_password_row.frequent_request_count
					last_reset_request = reset_password_row.ts_requested
					time_difference = now().timestamp() - last_reset_request.timestamp()

					temp_object = __import__("backend.models", fromlist=settings.MODEL_MAPPING["RESET_PASSWORD"]["model_class"])
					model_class = getattr(temp_object, settings.MODEL_MAPPING["RESET_PASSWORD"]["model_class"])
					resource_name = settings.MODEL_MAPPING["RESET_PASSWORD"]["resource_name"]

					if frequent_request_count >= settings.FREQUENT_REQUEST_COUNT_LIMIT and time_difference < settings.RESET_PASSWORD_INTERVAL:
						remaining_time = int((settings.RESET_PASSWORD_INTERVAL-time_difference)/60)
						raise ApplicationError(["request_limit_exceeded", remaining_time], resource_name=resource_name+"_verification_code")
					elif time_difference > settings.RESET_PASSWORD_INTERVAL:
						frequent_request_count = 1
					else:
						frequent_request_count = (frequent_request_count+1)%settings.RESET_PASSWORD_INTERVAL

					reset_code = generate_random_uuid()

					ResetPassword.objects.update_or_create(
						user_fk_id=user_fk_id,
						defaults={
							"reset_code": reset_code,
							"frequent_request_count": frequent_request_count,
							"ts_expiration_reset": now() + timedelta(seconds=settings.RESET_PASSWORD_INTERVAL),
							"ts_requested": now(),
							"ts_reset": None,
						}
					)

					signer = TimestampSigner()
					tmp_uuid = generate_random_uuid()
					signed_item = signer.sign(
						{
							"expiring_uuid": tmp_uuid
						}
					)

					signed_item_bytes = signed_item.encode("ascii")
					b64_signed_item_bytes = base64.b64encode(signed_item_bytes)
					b64_message = b64_signed_item_bytes.decode("ascii")
					expiring_reset_password_url = settings.RESET_PASSWORD_BASE_URL + "?cuxid=" + b64_message

					result = self.send_reset_code_email_task.apply_async(
						(email, reset_code, expiring_reset_password_url),
						countdown=settings.EMAIL_COUNTDOWN_SEC
					)
					Users.objects.filter(email=email).update(c_reset_task_id=result.id)
					log.debug("{} Will send reset code email to: {}. Updating async result with task ID: {}".format(
							request_details(request), email, result.id
						)
					)

					log.info("{} DB LOG".format(request_details(request)),
						extra={
							"api": self.class_name,
							"action": self.class_action,
							"data": model_to_json(req_data),
							"ip_address": get_ip_address(request),
						}
					)
					status_code, message = get_code_and_response(["success"])
					content = {}
					content[MESSAGE] = message
					content[RESOURCE_NAME] = "user"
					response = {}
					response[CONTENT] = content
					response[STATUS_CODE] = status_code
					log.debug("{} SUCCESS".format(request_details(request)))
					data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to request reset code via email"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class ResetAccountPassword(GenericAPIView):
	"""
	post:
	Resets the password if the provided password reset code matches the latest password reset code received via email
	"""
	class_name = "ResetAccountPassword"
	class_action = "UPDATE"
	serializer_class = ResetPasswordSerializer
	response_types = [
		["success"],
		["bad_request"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["resource_expired", "reset_code"],
		["resource_incorrect", "reset_code"],
		["resource_not_requested", "reset_code"],
		["internal_server_error"]
	]
	response_dict = build_fields("ResetAccountPassword", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}

			req_data = request.data
			req_obj = {
				"email": req_data.get("email"),
				"received_reset_code": req_data.get("reset_code"),
			}
			log.debug("{} START".format(request_details(request)))
			serialized_item = ResetPasswordSerializer(data=req_data)
			is_resource_reset = False

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					log.debug("{} VALID DATA".format(request_details(request)))
					email = req_data.get("email")
					password = req_data.get("password")
					received_reset_code = req_data.get("reset_code")
					ts_now = now()
					user_row = Users.objects.filter(email=email).values("id")

					if not user_row:
						raise ApplicationError(["resource_not_found", "user"])

					user_fk_id = user_row[0].get("id")
					reset_password_row = ResetPassword.objects.filter(user_fk_id=user_fk_id).first()

					if not reset_password_row:
						log.debug("{} No active reset code.".format(request_details(request)))
						raise ApplicationError(["resource_not_requested", "reset_code"], reason="not_requested_reset_code")
					
					if is_compliant(password) == False:
						log.debug("{} Password is not compliant with the password policy".format(request_details(request)))
						raise ApplicationError(["resource_incorrect", "password"])

					active_reset_code = reset_password_row.reset_code
					code_has_expired = reset_password_row.ts_expiration_reset.timestamp() < now().timestamp()

					if not reset_password_row is None and active_reset_code == received_reset_code and not code_has_expired:
						ts_now = now()
						log.debug("{} Reset password codes match.".format(request_details(request)))
						ResetPassword.objects.filter(user_fk_id=user_fk_id).update(
							ts_reset=ts_now,
							ts_expiration_reset=ts_now
						)
						password_hash = make_password(password)
						Users.objects.filter(email=email).update(
							password=password_hash
						)
						log.info("{} DB LOG".format(request_details(request)),
							extra={
								"user_id": user_fk_id,
								"api": self.class_name,
								"action": self.class_action,
								"data": model_to_json(req_obj),
								"ip_address": get_ip_address(request),
							}
						)
						status_code, message = get_code_and_response(["success"])
						content = {}
						content[MESSAGE] = message
						content[RESOURCE_NAME] = "password"
						response = {}
						response[CONTENT] = content
						response[STATUS_CODE] = status_code
						log.debug("{} SUCCESS".format(request_details(request)))
						data = response
					elif active_reset_code != received_reset_code:
						log.debug("{} Reset codes mismatch.".format(request_details(request)))
						raise ApplicationError(["resource_incorrect", "reset_code"], reason="incorrect_reset_code")
					else:
						log.debug("{} Reset code has expired.".format(request_details(request)))
						raise ApplicationError(["resource_expired", "reset_code"], reason="expired_reset_code")
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_obj),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to reset password"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class UpdatePassword(GenericAPIView):
	"""
	post:
	Updates the user's password
	"""
	class_name = "UpdatePassword"
	class_action = "UPDATE"
	serializer_class = UpdatePasswordSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["resource_incorrect", "password"],
		["internal_server_error"]
	]
	response_dict = build_fields("UpdatePassword", response_types)

	@swagger_auto_schema(
		responses=response_dict,
	)
	def post(self, request, *args, **kwargs):
		try:
			log.debug("{} START".format(request_details(request)))
			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			response = {}
			data = {}

			req_data = request.data
			serialized_item = UpdatePasswordSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))

				with transaction.atomic():
					current_user = payload["sub"]
					current_password = req_data.get("current_password")
					new_password = req_data.get("new_password")
					ts_now = now()

					user_obj = Users.objects.filter(id=payload["user_id"]).first()

					if not user_obj:
						raise ApplicationError(["resource_not_found", "user"])
					
					if is_compliant(new_password) == False:
						log.debug("{} Password is not compliant with the password policy".format(request_details(request)))
						raise ApplicationError(["resource_incorrect", "password"])

					password_hash = user_obj.password

					if not check_password(current_password, password_hash):
						log.debug("{} Password is incorrect".format(request_details(request)))
						raise ApplicationError(["resource_incorrect", "password"])
					else:
						new_password_hash = make_password(new_password)
						Users.objects.filter(
							id=payload["user_id"]
						).update(
							password=new_password_hash
						)
						log.info("{} DB LOG".format(request_details(request)),
							extra={
								"user_id": payload["user_id"],
								"api": self.class_name,
								"action": self.class_action,
								"ip_address": get_ip_address(request),
							}
						)
						status_code, message = get_code_and_response(["success"])
						content = {}
						content[MESSAGE] = message
						content[RESOURCE_NAME] = "user"
						response = {}
						response[CONTENT] = content
						response[STATUS_CODE] = status_code
						log.debug("{} SUCCESS".format(request_details(request)))
						data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to update password"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class UpdateProfile(GenericAPIView):
	"""
	post:
	Updates the user's profile details
	"""
	class_name = "UpdateProfile"
	class_action = "UPDATE"
	serializer_class = UpdateProfileSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("UpdateProfile", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request". format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = UpdateProfileSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					ts_now = now()
					cleanup_dirs_list = []

					user_obj = Users.objects.filter(id=payload["user_id"]).first()

					media_type_id = req_data.get("media_type_id", None)
					media_type = req_data.get("type", None)

					media_row_obj = MediaFile.objects.filter(
						media_type_uuid = media_type_id,
						media_type = media_type,
						is_file_synced = False,
					).first()

					if not media_row_obj:
						log.debug("{} Media row not found. Will skip profile picture update".format(request_details(request)))
					else:
						# HANDLE UPLOADED PROFILE PIC - START
						log.debug("{} Will handle uploaded media".format(request_details(request)))

						file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
										str(media_row_obj.dir_path) + "/" + str(media_row_obj.uuid) + str(media_row_obj.file_ext)

						if os.path.exists(file_to_move):
							new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
										str(media_row_obj.dir_path) + "/" + str(media_row_obj.uuid) + str(media_row_obj.file_ext)

							tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(media_row_obj.dir_path)

							if not os.path.exists(tmp_dir_path):
								os.makedirs(tmp_dir_path)

							pathlib.Path(file_to_move).rename(new_file_name)

							cleanup_dirs_list.append(
								DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(media_row_obj.dir_path)
							)

							MediaFile.objects.filter(
								uuid=media_row_obj.uuid,
							).delete()

							new_file_src = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(media_row_obj.dir_path) + "/" + str(media_row_obj.uuid) + str(media_row_obj.file_ext)

							user_obj.file_src = new_file_src
							user_obj.save()
						# HANDLE UPLOADED PROFILE PIC - END

					# HANDLE UPDATES OF FULL NAME AND TELEPHONE - START
					user_name = req_data.get("name", None)
					user_surname = req_data.get("surname", None)
					user_telephone = req_data.get("telephone", None)

					if user_name:
						user_obj.name = user_name
						user_obj.save()

					if user_surname:
						user_obj.surname = user_surname
						user_obj.save()

					user_obj.telephone = user_telephone
					user_obj.save()
					# HANDLE UPDATES OF FULL NAME AND TELEPHONE - END

					for dir_item in cleanup_dirs_list:
						try:
							shutil.rmtree(dir_item)
							log.debug("{} Media deleted: {}".format(request_details(request), dir_item))
						except Exception as e:
							log.debug("{} Media cannot be deleted. Error: {}".format(request_details(request), str(e)))

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "user"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to update profie"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresCreate(GenericAPIView):
	"""
	post:
	Creates a new ecclesiastical treasure
	"""
	class_name = "EcclesiasticalTreasuresCreate"
	class_action = "CREATE"
	serializer_class = EcclesiasticalTreasuresCreateSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresCreate", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request". format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresCreateSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					ts_now = now()
					treasure_uuid = generate_random_uuid()
					new_treasure = Ecclesiastical_Treasures(
						uuid=treasure_uuid,
						user_fk_id=payload["user_id"],
					)
					new_treasure.save()

					# LANGUAGE CODES - START
					lang_en_row = E56_Language.objects.filter(code="en").first()
					lang_en_fk_id = lang_en_row.id

					lang_gr_row = E56_Language.objects.filter(code="gr").first()
					lang_gr_fk_id = lang_gr_row.id

					lang_bg_row = E56_Language.objects.filter(code="bg").first()
					lang_bg_fk_id = lang_bg_row.id

					lang_tk_row = E56_Language.objects.filter(code="tk").first()
					lang_tk_fk_id = lang_tk_row.id
					# LANGUAGE CODES - END

					# TITLE - START
					title_en = req_data.get("title_en")

					new_title_en = E35_Title(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_en_fk_id,
						content=title_en,
						ts_added=ts_now,
					)
					new_title_en.save()

					title_gr = req_data.get("title_gr", None)

					new_title_gr = E35_Title(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_gr_fk_id,
						content=title_gr,
						ts_added=ts_now,
					)
					new_title_gr.save()

					title_bg = req_data.get("title_bg", None)

					new_title_bg = E35_Title(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_bg_fk_id,
						content=title_bg,
						ts_added=ts_now,
					)
					new_title_bg.save()

					title_tk = req_data.get("title_tk", None)

					new_title_tk = E35_Title(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_tk_fk_id,
						content=title_tk,
						ts_added=ts_now,
					)
					new_title_tk.save()
					# TITLE - END

					# APPELLATION - START
					appellation_en = req_data.get("appellation_en")

					new_appellation_en = E41_Appellation(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_en_fk_id,
						content=appellation_en,
						ts_added=ts_now,
					)
					new_appellation_en.save()

					appellation_gr = req_data.get("appellation_gr", None)

					new_appellation_gr = E41_Appellation(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_gr_fk_id,
						content=appellation_gr,
						ts_added=ts_now,
					)
					new_appellation_gr.save()

					appellation_bg = req_data.get("appellation_bg", None)

					new_appellation_bg = E41_Appellation(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_bg_fk_id,
						content=appellation_bg,
						ts_added=ts_now,
					)
					new_appellation_bg.save()

					appellation_tk = req_data.get("appellation_tk", None)

					new_appellation_tk = E41_Appellation(
						treasure_fk_id=new_treasure.uuid,
						language_fk_id=lang_tk_fk_id,
						content=appellation_tk,
						ts_added=ts_now,
					)
					new_appellation_tk.save()
					# APPELLATION - END

					# EXISTING OBJECT CODE - START
					existing_obj_code = req_data.get("existing_obj_code", None)

					new_identifier = E42_Identifier(
						treasure_fk_id=new_treasure.uuid,
						code=existing_obj_code,
						ts_added=ts_now,
					)
					new_identifier.save()
					# EXISTING OBJECT CODE - END

					# DESCRIPTION SHORT VERSION - START
					desc_short_version = req_data.get("desc_short_version", None)
					desc_extended_version = req_data.get("desc_extended_version", None)

					new_description = Description(
						treasure_fk_id=new_treasure.uuid,
						short_version=desc_short_version,
						extended_version=desc_extended_version,
						ts_added=ts_now,
					)
					new_description.save()
					# DESCRIPTION SHORT VERSION - END

					# TIME SPAN - START
					time_span = req_data.get("time_span", None)

					new_time_span = E52_Time_Span(
						treasure_fk_id=new_treasure.uuid,
						duration=time_span,
						ts_added=ts_now,
					)
					new_time_span.save()
					# TIME SPAN - END

					# KIND - START
					kind = req_data.get("kind", None)

					new_kind = E55_Type(
						treasure_fk_id=new_treasure.uuid,
						kind=kind,
						ts_added=ts_now,
					)
					new_kind.save()
					# KIND - END

					# CREATOR - START
					creator = req_data.get("creator", None)

					new_creator = E71_Human_Made_Thing(
						treasure_fk_id=new_treasure.uuid,
						creator=creator,
						ts_added=ts_now,
					)
					new_creator.save()
					# CREATOR - END

					# BEGINNING OF EXISTENCE - START
					beginning_of_existence = req_data.get("beginning_of_existence", None)

					new_beginning_of_existence = E63_Beginning_of_Existence(
						treasure_fk_id=new_treasure.uuid,
						content=beginning_of_existence,
						ts_added=ts_now,
					)
					new_beginning_of_existence.save()
					# BEGINNING OF EXISTENCE - END

					# BIOGRAPHY INFORMATION - START 
					was_in_church = req_data.get("was_in_church", False)
					was_in_another_country = req_data.get("was_in_another_country", False)
					was_lost_and_found = req_data.get("was_lost_and_found", False)

					if was_in_church == "false" or was_in_church == False:
						was_in_church = False
					else:
						was_in_church = True

					if was_in_another_country == "false" or was_in_another_country == False:
						was_in_another_country = False
					else:
						was_in_another_country = True

					if was_lost_and_found == "false" or was_lost_and_found == False:
						was_lost_and_found = False
					else:
						was_lost_and_found = True

					new_biography = Biography(
						treasure_fk_id=new_treasure.uuid,
						was_in_church=was_in_church,
						was_in_another_country=was_in_another_country,
						was_lost_and_found=was_lost_and_found,
						ts_added=ts_now,
					)
					new_biography.save()
					# BIOGRAPHY INFORMATION - END

					# DIMENSION - START
					dimension = req_data.get("dimension", None)

					new_dimension = E54_Dimension(
						treasure_fk_id=new_treasure.uuid,
						content=dimension,
						ts_added=ts_now,
					)
					new_dimension.save()
					# DIMENSION - END

					# MATERIAL - START
					material = req_data.get("material", None)

					new_material = E57_Material(
						treasure_fk_id=new_treasure.uuid,
						content=material,
						ts_added=ts_now,
					)
					new_material.save()
					# MATERIAL - END

					# INSCRIPTION - START
					inscription = req_data.get("inscription", None)

					new_inscription = E34_Inscription(
						treasure_fk_id=new_treasure.uuid,
						content=inscription,
						ts_added=ts_now,
					)
					new_inscription.save()
					# INSCRIPTION - END

					# MANUSCRIPT TEXT - START
					manuscript_text = req_data.get("manuscript_text", None)

					new_manuscript_text = E73_Information_Object(
						treasure_fk_id=new_treasure.uuid,
						content=manuscript_text,
						ts_added=ts_now,
					)
					new_manuscript_text.save()
					# MANUSCRIPT TEXT - END

					# EVENT INFORMATION - START
					event_information = req_data.get("event_information", None)

					new_event_information = E5_Event(
						treasure_fk_id=new_treasure.uuid,
						content=event_information,
						ts_added=ts_now,
					)
					new_event_information.save()
					# EVENT INFORMATION - END

					# PREVIOUS DOCUMENTATION - START
					previous_documentation = req_data.get("previous_documentation", None)
					relevant_bibliography = req_data.get("relevant_bibliography", None)

					new_documentation = Previous_Documentation(
						treasure_fk_id=new_treasure.uuid,
						documentation=previous_documentation,
						bibliography=relevant_bibliography,
						ts_added=ts_now,
					)
					new_documentation.save()
					# PREVIOUS DOCUMENTATION - END

					# PRESERVATION AND CONSERVATION STATUS - START
					preservation_status = req_data.get("preservation_status", None)
					conservation_status = req_data.get("conservation_status", None)

					new_preservation_status = E14_Condition_Assessment(
						treasure_fk_id=new_treasure.uuid,
						content=preservation_status,
						ts_added=ts_now,
					)
					new_preservation_status.save()

					new_conservation_status = E11_Modification(
						treasure_fk_id=new_treasure.uuid,
						content=conservation_status,
						ts_added=ts_now,
					)
					new_conservation_status.save()
					# PRESERVATION AND CONSERVATION STATUS - END

					# GROUP OF OBJECTS - START
					group_of_objects = req_data.get("group_of_objects", None)

					new_group_of_objects = E74_Group(
						treasure_fk_id=new_treasure.uuid,
						content=group_of_objects,
						ts_added=ts_now,
					)
					new_group_of_objects.save()
					# GROUP OF OBJECTS - END

					# COLLECTION IT BELONGS - START
					collection_it_belongs = req_data.get("collection_it_belongs", None)

					new_collection_it_belongs = E78_Curated_Holding(
						treasure_fk_id=new_treasure.uuid,
						content=collection_it_belongs,
						ts_added=ts_now,
					)
					new_collection_it_belongs.save()
					# COLLECTION IT BELONGS - END

					# POSITION - START
					position_of_treasure = req_data.get("position_of_treasure", None)

					new_position_of_treasure = E53_Place(
						treasure_fk_id=new_treasure.uuid,
						content=position_of_treasure,
						ts_added=ts_now,
					)
					new_position_of_treasure.save()
					# POSITION - END

					# DATA ADMINISTRATION - START
					people_that_help_with_documentation = req_data.get("people_that_help_with_documentation", None)

					new_data_admin = Data_Administration(
						treasure_fk_id=new_treasure.uuid,
						content=people_that_help_with_documentation,
						ts_added=ts_now,
					)
					new_data_admin.save()
					# DATA ADMINISTRATION - END

					cleanup_dirs_list = []

					# CONSERVATION PHOTOS - START
					conservation_photos_rows = MediaFile.objects.filter(
						media_type = "conservation",
						media_type_uuid = req_data.get("conservation_id", None),
						is_file_synced = False,
					)

					if conservation_photos_rows:
						log.debug("{} Will handle conservation photos".format(request_details(request)))

						for row_item in conservation_photos_rows:
							file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

							if os.path.exists(file_to_move):
								new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

								tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(row_item.dir_path)

								if not os.path.exists(tmp_dir_path):
									os.makedirs(tmp_dir_path)

								pathlib.Path(file_to_move).rename(new_file_name)

								img = Image.open(new_file_name)
								img = img.resize(
									(800, 600),
									Image.Resampling.LANCZOS
								)
								resized_image_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + str(row_item.file_ext)
								img.save(resized_image_name, format=img.format, quality=85)

								cleanup_dirs_list.append(
									DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(row_item.dir_path)
								)

								MediaFile.objects.filter(
									uuid = row_item.uuid,
									media_type = "conservation",
								).update(
									treasure_fk_id=new_treasure.uuid,
									is_file_synced = True,
									ts_synced = now(),
								)
					# CONSERVATION PHOTOS - END

					# CONTENT MEDIA - START
					content_rows = MediaFile.objects.filter(
						media_type = "content",
						media_type_uuid = req_data.get("content_id", None),
						is_file_synced = False,
					)

					if content_rows:
						log.debug("{} Will handle content media".format(request_details(request)))

						for row_item in content_rows:
							file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

							if os.path.exists(file_to_move):
								new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

								tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(row_item.dir_path)

								if not os.path.exists(tmp_dir_path):
									os.makedirs(tmp_dir_path)

								pathlib.Path(file_to_move).rename(new_file_name)

								img = Image.open(new_file_name)
								img = img.resize(
									(800, 600),
									Image.Resampling.LANCZOS
								)
								resized_image_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + str(row_item.file_ext)
								img.save(resized_image_name, format=img.format, quality=85)

								cleanup_dirs_list.append(
									DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(row_item.dir_path)
								)

								MediaFile.objects.filter(
									uuid = row_item.uuid,
									media_type = "content",
								).update(
									treasure_fk_id=new_treasure.uuid,
									is_file_synced = True,
									ts_synced = now(),
								)
					# CONTENT MEDIA - END

					# PHOTOS MEDIA - START
					photos_media_rows = MediaFile.objects.filter(
						media_type = "photo",
						media_type_uuid = req_data.get("photos_id", None),
						is_file_synced = False,
					)

					if photos_media_rows:
						log.debug("{} Will handle photos media".format(request_details(request)))

						for row_item in photos_media_rows:
							file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

							if os.path.exists(file_to_move):
								new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

								tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(row_item.dir_path)

								if not os.path.exists(tmp_dir_path):
									os.makedirs(tmp_dir_path)

								pathlib.Path(file_to_move).rename(new_file_name)

								img = Image.open(new_file_name)
								img = img.resize(
									(800, 600),
									Image.Resampling.LANCZOS
								)
								resized_image_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + str(row_item.file_ext)
								img.save(resized_image_name, format=img.format, quality=85)

								cleanup_dirs_list.append(
									DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(row_item.dir_path)
								)

								MediaFile.objects.filter(
									uuid = row_item.uuid,
									media_type = "photo",
								).update(
									treasure_fk_id=new_treasure.uuid,
									is_file_synced = True,
									ts_synced = now(),
								)
					# PHOTOS MEDIA - END

					# VIDEOS MEDIA - START
					videos_media_rows = MediaFile.objects.filter(
						media_type = "video",
						media_type_uuid = req_data.get("videos_id", None),
						is_file_synced = False,
					)

					if videos_media_rows:
						log.debug("{} Will handle videos media".format(request_details(request)))

						for row_item in videos_media_rows:
							file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

							if os.path.exists(file_to_move):
								new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

								tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(row_item.dir_path)

								if not os.path.exists(tmp_dir_path):
									os.makedirs(tmp_dir_path)

								pathlib.Path(file_to_move).rename(new_file_name)

								cleanup_dirs_list.append(
									DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(row_item.dir_path)
								)

								MediaFile.objects.filter(
									uuid = row_item.uuid,
									media_type = "video",
								).update(
									treasure_fk_id=new_treasure.uuid,
									is_file_synced = True,
									ts_synced = now(),
								)
					# VIDEOS MEDIA - END

					for dir_item in cleanup_dirs_list:
						try:
							shutil.rmtree(dir_item)
							log.debug("{} Media deleted: {}".format(request_details(request), dir_item))
						except Exception as e:
							log.debug("{} Media cannot be deleted. Error: {}".format(request_details(request), str(e)))

				req_data["treasure_id"] = treasure_uuid
				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "user"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to create ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresDelete(DestroyAPIView):
	"""
	delete:
	Delete data of an ecclesiastical treasure based on the `treasure_id`
	"""
	class_name = "EcclesiasticalTreasuresDelete"
	class_action = "DELETE"
	serializer_class = EcclesiasticalTreasuresDeleteSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_allowed"],
		["resource_not_found", "ecclesiastical_treasure"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"],
	]
	response_dict = build_fields("EcclesiasticalTreasuresDelete", response_types)
	treasure_id_param = openapi.Parameter(
		"treasure_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the ecclesiastical treasure you would like to delete",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[treasure_id_param]
	)
	def delete(self, request):
		try:
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			log.debug("{} START".format(request_details(request)))
			serialized_item = EcclesiasticalTreasuresDeleteSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=False)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				treasure_uuid = req_data.get("treasure_id")
				cleanup_dirs = []

				treasure_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_uuid).first()

				if not treasure_row:
					raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

				current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
				current_user_id = current_user_obj.id

				added_by_user_fk = treasure_row.user_fk_id
				user_row = Users.objects.filter(
					id=added_by_user_fk
				).first()

				if user_row:
					if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
						raise ApplicationError(["resource_not_allowed"])

				conservation_photos_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_uuid,
						media_type = "conservation",
						is_file_synced = True,
					)

				if conservation_photos_rows:
					for item in conservation_photos_rows:
						cleanup_dirs.append(
							DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(item.dir_path)
						)

				content_photos_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_uuid,
						media_type = "content",
						is_file_synced = True,
					)

				if content_photos_rows:
					for item in content_photos_rows:
						cleanup_dirs.append(
							DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(item.dir_path)
						)

				photos_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_uuid,
						media_type = "photo",
						is_file_synced = True,
					)

				if photos_rows:
					for item in photos_rows:
						cleanup_dirs.append(
							DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(item.dir_path)
						)

				video_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_uuid,
						media_type = "video",
						is_file_synced = True,
					)

				if video_rows:
					for item in video_rows:
						cleanup_dirs.append(
							DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(item.dir_path)
						)

				try:
					with transaction.atomic():
						treasure_row.delete()
				except Exception as e:
					log.debug("{} Failed to delete treasure from db. Error: {}".format(request_details(request), str(e)))
					raise

				for dir_item in cleanup_dirs:
					try:
						shutil.rmtree(dir_item)
					except Exception as e:
						log.debug("{} Failed to delete dir path of conservation photo for ecclesiastical treasure. Error: {}".format(request_details(request), str(e)))

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to delete ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresFetch(GenericAPIView):
	"""
	get:
	Returns the data of a specific ecclesiastical treasure based on the `treasure_id`
	"""
	class_name = "EcclesiasticalTreasuresFetch"
	class_action = "LIST"
	serializer_class = EcclesiasticalTreasuresFetchSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_found", "ecclesiastical_treasure"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresFetch", response_types)
	search_keyword = openapi.Parameter(
		"treasure_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the ecclesiastical treasure you would like to fetch",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[search_keyword,]
	)
	def get(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresFetchSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=False)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				treasure_id = req_data.get("treasure_id", None)

				treasure_obj_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_id).first()

				if not treasure_obj_row:
					raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

				result_obj = {}

				lang_en_row = E56_Language.objects.filter(code="en").first()
				lang_en_fk_id = lang_en_row.id

				lang_gr_row = E56_Language.objects.filter(code="gr").first()
				lang_gr_fk_id = lang_gr_row.id

				lang_bg_row = E56_Language.objects.filter(code="bg").first()
				lang_bg_fk_id = lang_bg_row.id

				lang_tk_row = E56_Language.objects.filter(code="tk").first()
				lang_tk_fk_id = lang_tk_row.id

				e5_event_content = ""
				e11_modification_content = ""
				e14_condition_assessment_content = ""
				e34_inscription_content = ""
				e35_title_en_content = ""
				e35_title_gr_content = ""
				e35_title_bg_content = ""
				e35_title_tk_content = ""
				e41_appellation_en_content = ""
				e41_appellation_gr_content = ""
				e41_appellation_bg_content = ""
				e41_appellation_tk_content = ""
				e42_identifier_content = ""
				e52_time_span_content = ""
				e53_place_content = ""
				e54_dimension_content = ""
				e55_type_content = ""
				e57_material_content = ""
				e63_beginning_of_existence_content = ""
				e71_human_made_thing_content = ""
				e73_information_object_content = ""
				e74_group_content = ""
				e78_curated_holding_content = ""
				description_short_content = ""
				description_extended_content = ""
				was_in_church = False
				was_in_another_country = False
				was_lost_and_found = False
				previous_documentation_content = ""
				relevant_bibliography_content = ""
				people_that_help_with_documentation_first = ""
				people_that_help_with_documentation_second = ""
				people_that_help_with_documentation_third = ""
				group_first = ""
				group_second = ""
				group_third = ""

				e5_event_row = E5_Event.objects.filter(treasure_fk_id=treasure_id).first()

				if e5_event_row:
					e5_event_content = e5_event_row.content

				e11_modification_row = E11_Modification.objects.filter(treasure_fk_id=treasure_id).first()

				if e11_modification_row:
					e11_modification_content = e11_modification_row.content

				e14_condition_assessment_row = E14_Condition_Assessment.objects.filter(treasure_fk_id=treasure_id).first()

				if e14_condition_assessment_row:
					e14_condition_assessment_content = e14_condition_assessment_row.content

				e34_inscription_row = E34_Inscription.objects.filter(treasure_fk_id=treasure_id).first()

				if e34_inscription_row:
					e34_inscription_content = e34_inscription_row.content

				e35_title_en_row = E35_Title.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_en_fk_id
				).first()

				if e35_title_en_row:
					e35_title_en_content = e35_title_en_row.content

				e35_title_gr_row = E35_Title.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_gr_fk_id
				).first()

				if e35_title_gr_row:
					e35_title_gr_content = e35_title_gr_row.content

				e35_title_bg_row = E35_Title.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_bg_fk_id
				).first()

				if e35_title_bg_row:
					e35_title_bg_content = e35_title_bg_row.content

				e35_title_tk_row = E35_Title.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_tk_fk_id
				).first()

				if e35_title_tk_row:
					e35_title_tk_content = e35_title_tk_row.content

				e41_appellation_en_row = E41_Appellation.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_en_fk_id
				).first()

				if e41_appellation_en_row:
					e41_appellation_en_content = e41_appellation_en_row.content

				e41_appellation_gr_row = E41_Appellation.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_gr_fk_id
				).first()

				if e41_appellation_gr_row:
					e41_appellation_gr_content = e41_appellation_gr_row.content

				e41_appellation_bg_row = E41_Appellation.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_bg_fk_id
				).first()

				if e41_appellation_bg_row:
					e41_appellation_bg_content = e41_appellation_bg_row.content

				e41_appellation_tk_row = E41_Appellation.objects.filter(
					treasure_fk_id=treasure_id,
					language_fk_id=lang_tk_fk_id
				).first()

				if e41_appellation_tk_row:
					e41_appellation_tk_content = e41_appellation_tk_row.content

				e42_identifier_row = E42_Identifier.objects.filter(treasure_fk_id=treasure_id).first()

				if e42_identifier_row:
					e42_identifier_content = e42_identifier_row.code

				e52_time_span_row = E52_Time_Span.objects.filter(treasure_fk_id=treasure_id).first()

				if e52_time_span_row:
					e52_time_span_content = e52_time_span_row.duration

				e53_place_row = E53_Place.objects.filter(treasure_fk_id=treasure_id).first()

				if e53_place_row:
					e53_place_content = e53_place_row.content

				e54_dimension_row = E54_Dimension.objects.filter(treasure_fk_id=treasure_id).first()

				if e54_dimension_row:
					e54_dimension_content = e54_dimension_row.content

				e55_type_row = E55_Type.objects.filter(treasure_fk_id=treasure_id).first()

				if e55_type_row:
					e55_type_content = e55_type_row.kind

				e57_material_row = E57_Material.objects.filter(treasure_fk_id=treasure_id).first()

				if e57_material_row:
					e57_material_content = e57_material_row.content

				e63_beginning_of_existence_row = E63_Beginning_of_Existence.objects.filter(treasure_fk_id=treasure_id).first()

				if e63_beginning_of_existence_row:
					e63_beginning_of_existence_content = e63_beginning_of_existence_row.content

				e71_human_made_thing_row = E71_Human_Made_Thing.objects.filter(treasure_fk_id=treasure_id).first()

				if e71_human_made_thing_row:
					e71_human_made_thing_content = e71_human_made_thing_row.creator

				e73_information_object_row = E73_Information_Object.objects.filter(treasure_fk_id=treasure_id).first()

				if e73_information_object_row:
					e73_information_object_content = e73_information_object_row.content

				e74_group_row = E74_Group.objects.filter(treasure_fk_id=treasure_id).first()

				if e74_group_row:
					e74_group_content = e74_group_row.content

					if e74_group_content:
						group_len = len(e74_group_content)

						if group_len == 1:
							group_first = e74_group_content[0]
						elif group_len == 2:
							group_first = e74_group_content[0]
							group_second = e74_group_content[1]
						elif group_len == 3:
							group_first = e74_group_content[0]
							group_second = e74_group_content[1]
							group_third = e74_group_content[2]

				e78_curated_holding_row = E78_Curated_Holding.objects.filter(treasure_fk_id=treasure_id).first()

				if e78_curated_holding_row:
					e78_curated_holding_content = e78_curated_holding_row.content

				description_short_row = Description.objects.filter(treasure_fk_id=treasure_id).first()

				if description_short_row:
					description_short_content = description_short_row.short_version

				description_extended_row = Description.objects.filter(treasure_fk_id=treasure_id).first()

				if description_extended_row:
					description_extended_content = description_extended_row.extended_version

				biorgraphy_row = Biography.objects.filter(treasure_fk_id=treasure_id).first()

				if biorgraphy_row:
					was_in_church = biorgraphy_row.was_in_church
					was_in_another_country = biorgraphy_row.was_in_another_country
					was_lost_and_found = biorgraphy_row.was_lost_and_found

				previous_documentation_row = Previous_Documentation.objects.filter(treasure_fk_id=treasure_id).first()

				if previous_documentation_row:
					previous_documentation_content = previous_documentation_row.documentation
					relevant_bibliography_content = previous_documentation_row.bibliography

				people_that_help_with_documentation_row = Data_Administration.objects.filter(treasure_fk_id=treasure_id).first()

				if people_that_help_with_documentation_row:
					people_that_help_with_documentation_content = people_that_help_with_documentation_row.content

					if people_that_help_with_documentation_content:
						people_len = len(people_that_help_with_documentation_content)

						if people_len == 1:
							people_that_help_with_documentation_first = people_that_help_with_documentation_content[0]
						elif people_len == 2:
							people_that_help_with_documentation_first = people_that_help_with_documentation_content[0]
							people_that_help_with_documentation_second = people_that_help_with_documentation_content[1]
						elif people_len == 3:
							people_that_help_with_documentation_first = people_that_help_with_documentation_content[0]
							people_that_help_with_documentation_second = people_that_help_with_documentation_content[1]
							people_that_help_with_documentation_third = people_that_help_with_documentation_content[2]

				result_obj["user_email"] = ""
				result_obj["user_organization"] = ""
				result_obj["is_editable"] = False

				current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
				current_user_id = current_user_obj.id
				added_by_user_fk = treasure_obj_row.user_fk_id
				user_row = Users.objects.filter(
					id=added_by_user_fk
				).first()

				if user_row:
					result_obj["user_email"] = user_row.email
					result_obj["user_organization"] = user_row.organization

					if current_user_id == added_by_user_fk or current_user_obj.role == RoleModel.ADMIN:
						result_obj["is_editable"] = True
					else:
						result_obj["is_editable"] = False

				result_obj["e5_event_content"] = e5_event_content
				result_obj["e11_modification_content"] = e11_modification_content
				result_obj["e14_condition_assessment_content"] = e14_condition_assessment_content
				result_obj["e34_inscription_content"] = e34_inscription_content
				result_obj["e35_title_en_content"] = e35_title_en_content
				result_obj["e35_title_gr_content"] = e35_title_gr_content
				result_obj["e35_title_bg_content"] = e35_title_bg_content
				result_obj["e35_title_tk_content"] = e35_title_tk_content
				result_obj["e41_appellation_en_content"] = e41_appellation_en_content
				result_obj["e41_appellation_gr_content"] = e41_appellation_gr_content
				result_obj["e41_appellation_bg_content"] = e41_appellation_bg_content
				result_obj["e41_appellation_tk_content"] = e41_appellation_tk_content
				result_obj["e42_identifier_content"] = e42_identifier_content
				result_obj["e52_time_span_content"] = e52_time_span_content
				result_obj["e53_place_content"] = e53_place_content
				result_obj["e54_dimension_content"] = e54_dimension_content
				result_obj["e55_type_content"] = e55_type_content
				result_obj["e57_material_content"] = e57_material_content
				result_obj["e63_beginning_of_existence_content"] = e63_beginning_of_existence_content
				result_obj["e71_human_made_thing_content"] = e71_human_made_thing_content
				result_obj["e73_information_object_content"] = e73_information_object_content
				result_obj["group_first"] = group_first
				result_obj["group_second"] = group_second
				result_obj["group_third"] = group_third
				result_obj["e78_curated_holding_content"] = e78_curated_holding_content
				result_obj["description_short_content"] = description_short_content
				result_obj["description_extended_content"] = description_extended_content
				result_obj["was_in_church"] = was_in_church
				result_obj["was_in_another_country"] = was_in_another_country
				result_obj["was_lost_and_found"] = was_lost_and_found
				result_obj["previous_documentation_content"] = previous_documentation_content
				result_obj["relevant_bibliography_content"] = relevant_bibliography_content
				result_obj["people_that_help_with_documentation_first"] = people_that_help_with_documentation_first
				result_obj["people_that_help_with_documentation_second"] = people_that_help_with_documentation_second
				result_obj["people_that_help_with_documentation_third"] = people_that_help_with_documentation_third

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_OBJ] = result_obj
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to fetch ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresList(GenericAPIView):
	"""
	get:
	Returns the list of all ecclesiastical treasures based on the `search_keyword` and `exact_match` if given
	"""
	class_name = "EcclesiasticalTreasuresList"
	class_action = "LIST"
	serializer_class = EcclesiasticalTreasuresListSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresList", response_types)
	search_keyword = openapi.Parameter(
		"search_keyword",
		in_=openapi.IN_QUERY,
		description="The search keyword to filter ecclesiastical treasures",
		type=openapi.TYPE_STRING,
		required=False,
	)
	exact_match = openapi.Parameter(
		"exact_match",
		in_=openapi.IN_QUERY,
		description="Whether the search keyword to be exact match or not when filtering ecclesiastical treasures",
		type=openapi.TYPE_BOOLEAN,
		required=False,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[search_keyword, exact_match,]
	)
	def get(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresListSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=False)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				search_keyword = req_data.get("search_keyword", None)
				exact_match = req_data.get("exact_match", False)

				if exact_match == "true":
					exact_match = True
				else:
					exact_match = False

				list_results = []
				filtered_uuids = []

				if not search_keyword:
					item_rows = Ecclesiastical_Treasures.objects.all()

					for item in item_rows:
						filtered_uuids.append(item.uuid)
				else:
					########################################################
					# Filter based on `search_keyword` and `exact_match` in all models - START

					# Filter based on treasure `uuid`
					treasure_by_uuid_rows = Ecclesiastical_Treasures.objects.filter(Q(**{"uuid": search_keyword}) if exact_match else Q(**{f"{'uuid'}__icontains": search_keyword}))

					for item in treasure_by_uuid_rows:
						filtered_uuids.append(item.uuid)

					# Filter based on user's `email`
					user_email_rows = Users.objects.filter(Q(**{"email": search_keyword}) if exact_match else Q(**{f"{'email'}__icontains": search_keyword}))

					for item in user_email_rows:
						user_id = item.id
						treasure_by_email_rows = Ecclesiastical_Treasures.objects.filter(
							user_fk_id=user_id
						)

						for treasure_item in treasure_by_email_rows:
							filtered_uuids.append(treasure_item.uuid)

					# Filter based on user's `name`
					user_name_rows = Users.objects.filter(Q(**{"name": search_keyword}) if exact_match else Q(**{f"{'name'}__icontains": search_keyword}))

					for item in user_name_rows:
						user_id = item.id
						treasure_by_name_rows = Ecclesiastical_Treasures.objects.filter(
							user_fk_id=user_id
						)

						for treasure_item in treasure_by_name_rows:
							filtered_uuids.append(treasure_item.uuid)

					# Filter based on user's `surname`
					user_surname_rows = Users.objects.filter(Q(**{"surname": search_keyword}) if exact_match else Q(**{f"{'surname'}__icontains": search_keyword}))

					for item in user_surname_rows:
						user_id = item.id
						treasure_by_surname_rows = Ecclesiastical_Treasures.objects.filter(
							user_fk_id=user_id
						)

						for treasure_item in treasure_by_surname_rows:
							filtered_uuids.append(treasure_item.uuid)

					# Filter based on user's `telephone`
					user_telephone_rows = Users.objects.filter(Q(**{"telephone": search_keyword}) if exact_match else Q(**{f"{'telephone'}__icontains": search_keyword}))

					for item in user_telephone_rows:
						user_id = item.id
						treasure_by_telephone_rows = Ecclesiastical_Treasures.objects.filter(
							user_fk_id=user_id
						)

						for treasure_item in treasure_by_telephone_rows:
							filtered_uuids.append(treasure_item.uuid)

					# Filter based on user's `organization`
					user_organization_rows = Users.objects.filter(Q(**{"organization": search_keyword}) if exact_match else Q(**{f"{'organization'}__icontains": search_keyword}))

					for item in user_organization_rows:
						user_id = item.id
						treasure_by_organization_rows = Ecclesiastical_Treasures.objects.filter(
							user_fk_id=user_id
						)

						for treasure_item in treasure_by_organization_rows:
							filtered_uuids.append(treasure_item.uuid)

					# Filter based on `E5_Event`
					e5_event_rows = E5_Event.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e5_event_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E11_Modification`
					e11_modification_rows = E11_Modification.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e11_modification_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E14_Condition_Assessment`
					e14_condition_assessment_rows = E14_Condition_Assessment.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e14_condition_assessment_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E34_Inscription`
					e34_inscription_rows = E34_Inscription.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e34_inscription_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E35_Title`
					e35_title_rows = E35_Title.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e35_title_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E41_Appellation`
					e41_appellation_rows = E41_Appellation.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e41_appellation_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E42_Identifier`
					e42_identifier_rows = E42_Identifier.objects.filter(Q(**{"code": search_keyword}) if exact_match else Q(**{f"{'code'}__icontains": search_keyword}))

					for item in e42_identifier_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E52_Time_Span`
					e52_time_span_rows = E52_Time_Span.objects.filter(Q(**{"duration": search_keyword}) if exact_match else Q(**{f"{'duration'}__icontains": search_keyword}))

					for item in e52_time_span_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E53_Place`
					e53_place_rows = E53_Place.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e53_place_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E54_Dimension`
					e54_dimension_rows = E54_Dimension.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e54_dimension_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E55_Type`
					e55_type_rows = E55_Type.objects.filter(Q(**{"kind": search_keyword}) if exact_match else Q(**{f"{'kind'}__icontains": search_keyword}))

					for item in e55_type_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E57_Material`
					e57_material_rows = E57_Material.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e57_material_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E63_Beginning_of_Existence`
					e63_beginning_of_existence_rows = E63_Beginning_of_Existence.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e63_beginning_of_existence_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E71_Human_Made_Thing`
					e71_human_made_thing_rows = E71_Human_Made_Thing.objects.filter(Q(**{"creator": search_keyword}) if exact_match else Q(**{f"{'creator'}__icontains": search_keyword}))

					for item in e71_human_made_thing_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E73_Information_Object`
					e73_information_object_rows = E73_Information_Object.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e73_information_object_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E74_Group`
					e74_group_rows = E74_Group.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e74_group_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `E78_Curated_Holding`
					e78_curated_holding_rows = E78_Curated_Holding.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in e78_curated_holding_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `Data_Administration`
					data_admin_rows = Data_Administration.objects.filter(Q(**{"content": search_keyword}) if exact_match else Q(**{f"{'content'}__icontains": search_keyword}))

					for item in data_admin_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on short version of `Description`
					description_short_version_rows = Description.objects.filter(Q(**{"short_version": search_keyword}) if exact_match else Q(**{f"{'short_version'}__icontains": search_keyword}))

					for item in description_short_version_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on extended version of `Description`
					description_extended_version_rows = Description.objects.filter(Q(**{"extended_version": search_keyword}) if exact_match else Q(**{f"{'extended_version'}__icontains": search_keyword}))

					for item in description_extended_version_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on documentation of `Pieces_of_Ecclesiastical_Treasure`
					pieces_of_treasure_documentation_rows = Pieces_of_Ecclesiastical_Treasure.objects.filter(Q(**{"documentation": search_keyword}) if exact_match else Q(**{f"{'documentation'}__icontains": search_keyword}))

					for item in pieces_of_treasure_documentation_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on bibliography of `Pieces_of_Ecclesiastical_Treasure`
					pieces_of_treasure_bibliography_rows = Pieces_of_Ecclesiastical_Treasure.objects.filter(Q(**{"bibliography": search_keyword}) if exact_match else Q(**{f"{'bibliography'}__icontains": search_keyword}))

					for item in pieces_of_treasure_bibliography_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on documentation of `Previous_Documentation`
					prev_documentation_rows = Previous_Documentation.objects.filter(Q(**{"documentation": search_keyword}) if exact_match else Q(**{f"{'documentation'}__icontains": search_keyword}))

					for item in prev_documentation_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on bibliography of `Previous_Documentation`
					prev_documentation_bibliography_rows = Previous_Documentation.objects.filter(Q(**{"bibliography": search_keyword}) if exact_match else Q(**{f"{'bibliography'}__icontains": search_keyword}))

					for item in prev_documentation_bibliography_rows:
						filtered_uuids.append(item.treasure_fk_id)

					# Filter based on `search_keyword` and `exact_match` in all models - END
					########################################################

				lang_en_row = E56_Language.objects.filter(code="en").first()
				lang_en_fk_id = lang_en_row.id

				filtered_uuids = list(set(filtered_uuids))

				current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
				current_user_id = current_user_obj.id

				for item in filtered_uuids:
					current_item = {}
					current_item["uuid"] = item
					current_item["user_email"] = ""
					current_item["user_organization"] = ""
					current_item["is_editable"] = False

					treasure_row = Ecclesiastical_Treasures.objects.filter(uuid=item).first()

					if treasure_row:
						added_by_user_fk = treasure_row.user_fk_id
						user_row = Users.objects.filter(
							id=added_by_user_fk
						).first()

						if user_row:
							current_item["user_email"] = user_row.email
							current_item["user_organization"] = user_row.organization

							if current_user_id == added_by_user_fk or current_user_obj.role == RoleModel.ADMIN:
								current_item["is_editable"] = True
							else:
								current_item["is_editable"] = False

					title_row = E35_Title.objects.filter(
						treasure_fk_id=item,
						language_fk_id=lang_en_fk_id,
					).first()

					current_item["title_en"] = title_row.content

					appellation_row = E41_Appellation.objects.filter(
						treasure_fk_id=item,
						language_fk_id=lang_en_fk_id,
					).first()

					current_item["appellation_en"] = appellation_row.content

					# Set a default photo for the treasure by checking the following order:
					# - General photos
					# - Content photos
					# - Conservation photos
					default_img_src = None

					# Check for general photos
					photos_rows = MediaFile.objects.filter(
						treasure_fk_id = item,
						media_type = "photo",
						is_file_synced = True
					).order_by("ts_synced")

					if photos_rows:
						file_ext_split = photos_rows[0].file_ext.split(".")

						if file_ext_split[1] in settings.MEDIA_FORMAT_2D:
							default_img_src = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(photos_rows[0].dir_path) + "/" + str(photos_rows[0].uuid) + "_resized" + str(photos_rows[0].file_ext)

					# Check for content photos
					if not default_img_src:
						photos_rows = MediaFile.objects.filter(
							treasure_fk_id = item,
							media_type = "content",
							is_file_synced = True
						).order_by("ts_synced")

						if photos_rows:
							file_ext_split = photos_rows[0].file_ext.split(".")

							if file_ext_split[1] in settings.MEDIA_FORMAT_2D:
								default_img_src = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
											str(photos_rows[0].dir_path) + "/" + str(photos_rows[0].uuid) + "_resized" + str(photos_rows[0].file_ext)

					# Check for conservation photos
					if not default_img_src:
						photos_rows = MediaFile.objects.filter(
							treasure_fk_id = item,
							media_type = "conservation",
							is_file_synced = True
						).order_by("ts_synced")

						if photos_rows:
							file_ext_split = photos_rows[0].file_ext.split(".")

							if file_ext_split[1] in settings.MEDIA_FORMAT_2D:
								default_img_src = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
											str(photos_rows[0].dir_path) + "/" + str(photos_rows[0].uuid) + "_resized" + str(photos_rows[0].file_ext)

					# Finally, use a default image if none was found neither in general photos nor in conservation photos
					if not default_img_src:
						default_img_src = "/static/backend/assets/media/media_default.png"

					current_item["default_img_src"] = default_img_src

					if current_item["user_organization"] == payload["organization"]:
						list_results.insert(0, current_item)
					else:
						list_results.append(current_item)

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)

				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_ARRAY] = list_results
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to list ecclesiastical treasures"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresMediaDelete(DestroyAPIView):
	"""
	delete:
	Delete media file of an ecclesiastical treasure based on the `uuid`
	"""
	class_name = "EcclesiasticalTreasuresMediaDelete"
	class_action = "DELETE"
	serializer_class = EcclesiasticalTreasuresMediaDeleteSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_allowed"],
		["resource_not_found", "ecclesiastical_treasure"],
		["resource_not_found", "media_file"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"],
	]
	response_dict = build_fields("EcclesiasticalTreasuresMediaDelete", response_types)
	treasure_id_param = openapi.Parameter(
		"treasure_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the ecclesiastical treasure",
		type=openapi.TYPE_STRING,
		required=True,
	)
	media_id_param = openapi.Parameter(
		"media_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the media file you would like to delete",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[treasure_id_param, media_id_param]
	)
	def delete(self, request):
		try:
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			log.debug("{} START".format(request_details(request)))
			serialized_item = EcclesiasticalTreasuresMediaDeleteSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=False)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				treasure_uuid = req_data.get("treasure_id")
				media_uuid = req_data.get("media_id")
				cleanup_dir = ""

				treasure_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_uuid).first()

				if not treasure_row:
					raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

				current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
				current_user_id = current_user_obj.id

				added_by_user_fk = treasure_row.user_fk_id
				user_row = Users.objects.filter(
					id=added_by_user_fk
				).first()

				if user_row:
					if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
						raise ApplicationError(["resource_not_allowed"])

				with transaction.atomic():
					media_row = MediaFile.objects.filter(
							treasure_fk_id = treasure_uuid,
							uuid = media_uuid,
							is_file_synced = True,
						).first()

					if media_row:
						cleanup_dir = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(media_row.dir_path)
						media_row.delete()
					else:
						raise ApplicationError(["resource_not_found", "media_file"])	

				try:
					shutil.rmtree(cleanup_dir)
				except Exception as e:
					log.debug("{} Failed to delete dir path of media. Error: {}".format(request_details(request), str(e)))

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to delete media of ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresMediaList(GenericAPIView):
	"""
	get:
	Returns the list of all media for the given ecclesiastical treasure based on the `treasure_id`
	"""
	class_name = "EcclesiasticalTreasuresMediaList"
	class_action = "LIST"
	serializer_class = EcclesiasticalTreasuresMediaListSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_found", "ecclesiastical_treasure"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresMediaList", response_types)
	treasure_id_param = openapi.Parameter(
		"treasure_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the ecclesiastical treasure for which you would like to get its media files",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[treasure_id_param,]
	)
	def get(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresMediaListSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=False)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				log.debug("{} VALID DATA".format(request_details(request)))
				treasure_id = req_data.get("treasure_id", None)

				treasure_obj_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_id).first()

				if not treasure_obj_row:
					raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

				current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
				current_user_id = current_user_obj.id
				added_by_user_fk = treasure_obj_row.user_fk_id
				is_editable = False

				user_row = Users.objects.filter(
					id=added_by_user_fk
				).first()

				if user_row:
					if current_user_id == added_by_user_fk or current_user_obj.role == RoleModel.ADMIN:
						is_editable = True
					else:
						is_editable = False

				list_results = []

				conservation_photos_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_id,
						media_type = "conservation",
						is_file_synced = True,
					)

				if conservation_photos_rows:
					for row_item in conservation_photos_rows:
						file_ext = str(row_item.file_ext)
						file_src = DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + file_ext

						if file_ext[1:] in settings.MEDIA_IMAGE_2D:
							thumbnail = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + file_ext
						else:
							thumbnail = "/static/backend/assets/media/media_default.png"

						current_item = {
							"uuid": row_item.uuid,
							"media_type": row_item.media_type,
							"file_src": file_src,
							"thumbnail": thumbnail,
							"is_editable": is_editable,
						}
						list_results.append(current_item)

				content_media_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_id,
						media_type = "content",
						is_file_synced = True,
					)

				if content_media_rows:
					for row_item in content_media_rows:
						file_ext = str(row_item.file_ext)
						file_src = DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + file_ext

						if file_ext[1:] in settings.MEDIA_IMAGE_2D: 
							thumbnail = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + file_ext
						else:
							thumbnail = "/static/backend/assets/media/media_default.png"

						current_item = {
							"uuid": row_item.uuid,
							"media_type": row_item.media_type,
							"file_src": file_src,
							"thumbnail": thumbnail,
							"is_editable": is_editable,
						}
						list_results.append(current_item)

				photos_media_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_id,
						media_type = "photo",
						is_file_synced = True,
					)

				if photos_media_rows:
					for row_item in photos_media_rows:
						file_ext = str(row_item.file_ext)
						file_src = DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + file_ext

						if file_ext[1:] in settings.MEDIA_IMAGE_2D: 
							thumbnail = "/backend" + DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + file_ext
						else:
							thumbnail = "/static/backend/assets/media/media_default.png"

						current_item = {
							"uuid": row_item.uuid,
							"media_type": row_item.media_type,
							"file_src": file_src,
							"thumbnail": thumbnail,
							"is_editable": is_editable,
						}
						list_results.append(current_item)

				videos_media_rows = MediaFile.objects.filter(
						treasure_fk_id = treasure_id,
						media_type = "video",
						is_file_synced = True,
					)

				if videos_media_rows:
					for row_item in videos_media_rows:
						file_ext = str(row_item.file_ext)
						file_src = DIR_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + file_ext

						if file_ext[1:] in settings.MEDIA_IMAGE_2D: 
							thumbnail = "/backend" + file_src
						else:
							thumbnail = "/static/backend/assets/media/media_default.png"

						current_item = {
							"uuid": row_item.uuid,
							"media_type": row_item.media_type,
							"file_src": file_src,
							"thumbnail": thumbnail,
							"is_editable": is_editable,
						}
						list_results.append(current_item)

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_ARRAY] = list_results
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to list media of ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresMediaUpdate(GenericAPIView):
	"""
	post:
	Updates the media file of an ecclesiastical treasure
	"""
	class_name = "EcclesiasticalTreasuresMediaUpdate"
	class_action = "UPDATE"
	serializer_class = EcclesiasticalTreasuresMediaUpdateSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_allowed"],
		["resource_not_found", "ecclesiastical_treasure"],
		["resource_not_found", "media_file"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresMediaUpdate", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request". format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresMediaUpdateSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					ts_now = now()

					treasure_uuid = req_data.get("treasure_id")
					treasure_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_uuid).first()

					if not treasure_row:
						raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

					current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
					current_user_id = current_user_obj.id

					added_by_user_fk = treasure_row.user_fk_id
					user_row = Users.objects.filter(
						id=added_by_user_fk
					).first()

					if user_row:
						if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
							raise ApplicationError(["resource_not_allowed"])

					old_media_uuid = req_data.get("old_media_id")
					new_media_uuid = req_data.get("new_media_id")

					old_media_row = MediaFile.objects.filter(
						treasure_fk_id = treasure_uuid,
						uuid = old_media_uuid,
						is_file_synced = True,
					).first()

					if not old_media_row:
						raise ApplicationError(["resource_not_found", "media_file"])

					new_media_row = MediaFile.objects.filter(
						uuid = new_media_uuid,
						is_file_synced = False,
					).first()

					if not new_media_row:
						raise ApplicationError(["resource_not_found", "media_file"])

					old_file_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(old_media_row.dir_path) + "/" + str(old_media_row.uuid) + str(old_media_row.file_ext)

					new_file_path = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
											str(new_media_row.dir_path) + "/" + str(new_media_row.uuid) + str(new_media_row.file_ext)

					new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
											str(old_media_row.dir_path) + "/" + str(old_media_row.uuid) + str(new_media_row.file_ext)

					try:
						shutil.move(new_file_path, new_file_name)

						img = Image.open(new_file_name)
						img = img.resize(
							(800, 600),
							Image.Resampling.LANCZOS
						)
						resized_image_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
												str(old_media_row.dir_path) + "/" + str(old_media_row.uuid) + "_resized" + str(new_media_row.file_ext)
						img.save(resized_image_name, format=img.format, quality=85)

						if old_media_row.file_ext != new_media_row.file_ext:
							os.remove(old_file_path)
							old_media_row.file_ext = new_media_row.file_ext
							old_media_row.ts_synced = now()
							old_media_row.save()
							log.debug("{} Updated media file extension".format(request_details(request)))

						new_media_row.delete()
						log.debug("{} Updated old media file with new media file".format(request_details(request)))
					except Exception as e:
						log.debug("{} Failed to update old media file with new media file. Reason: {}".format(request_details(request), str(e)))
						raise

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "media_file"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to update media of ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresMediaUploadNew(GenericAPIView):
	"""
	post:
	Uploads new media for an ecclesiastical treasure
	"""
	class_name = "EcclesiasticalTreasuresMediaUploadNew"
	class_action = "UPLOAD"
	serializer_class = EcclesiasticalTreasuresMediaUploadNewSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_allowed"],
		["resource_not_found", "ecclesiastical_treasure"],
		["resource_not_found", "media_file"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresMediaUploadNew", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request". format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresMediaUploadNewSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					ts_now = now()
					cleanup_dirs_list = []

					treasure_id = req_data.get("treasure_id", None)
					treasure_row = Ecclesiastical_Treasures.objects.filter(uuid=treasure_id).first()

					if not treasure_row:
						raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

					current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
					current_user_id = current_user_obj.id

					added_by_user_fk = treasure_row.user_fk_id
					user_row = Users.objects.filter(
						id=added_by_user_fk
					).first()

					if user_row:
						if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
							raise ApplicationError(["resource_not_allowed"])

					media_type_id = req_data.get("media_type_id", None)
					media_type = req_data.get("type", None)

					media_rows = MediaFile.objects.filter(
						media_type_uuid = media_type_id,
						is_file_synced = False,
					)

					if not media_rows:
						raise ApplicationError(["resource_not_found", "media_file"])

					log.debug("{} Will handle uploaded media".format(request_details(request)))

					for row_item in media_rows:
						file_to_move = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

						if os.path.exists(file_to_move):
							new_file_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + str(row_item.file_ext)

							tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + str(row_item.dir_path)

							if not os.path.exists(tmp_dir_path):
								os.makedirs(tmp_dir_path)

							pathlib.Path(file_to_move).rename(new_file_name)

							img = Image.open(new_file_name)
							img = img.resize(
								(800, 600),
								Image.Resampling.LANCZOS
							)
							resized_image_name = DIR_CODE_MEDIA + DIR_MEDIA_SYNCED + \
										str(row_item.dir_path) + "/" + str(row_item.uuid) + "_resized" + str(row_item.file_ext)
							img.save(resized_image_name, format=img.format, quality=85)

							cleanup_dirs_list.append(
								DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(row_item.dir_path)
							)

							MediaFile.objects.filter(
								uuid = row_item.uuid,
							).update(
								media_type = media_type,
								treasure_fk_id = treasure_id,
								is_file_synced = True,
								ts_synced = now(),
							)

					for dir_item in cleanup_dirs_list:
						try:
							shutil.rmtree(dir_item)
							log.debug("{} Media deleted: {}".format(request_details(request), dir_item))
						except Exception as e:
							log.debug("{} Media cannot be deleted. Error: {}".format(request_details(request), str(e)))

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "media_file"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to upload media of ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class EcclesiasticalTreasuresUpdate(GenericAPIView):
	"""
	post:
	Updates an ecclesiastical treasure
	"""
	class_name = "EcclesiasticalTreasuresUpdate"
	class_action = "UPDATE"
	serializer_class = EcclesiasticalTreasuresUpdateSerializer
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_allowed"],
		["resource_not_found", "ecclesiastical_treasure"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("EcclesiasticalTreasuresUpdate", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[]
	)
	def post(self, request, *args, **kwargs):
		log.debug("{} Received request". format(request_details(request)))
		data = {}
		response = {}

		try:
			log.debug("{} START".format(request_details(request)))
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			serialized_item = EcclesiasticalTreasuresUpdateSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					ts_now = now()
					treasure_uuid = req_data.get("uuid")

					treasure_row = Ecclesiastical_Treasures.objects.filter(
						uuid=treasure_uuid,
					).first()

					if not treasure_row:
						raise ApplicationError(["resource_not_found", "ecclesiastical_treasure"])

					current_user_obj = Users.objects.filter(id=payload["user_id"]).first()
					current_user_id = current_user_obj.id

					added_by_user_fk = treasure_row.user_fk_id
					user_row = Users.objects.filter(
						id=added_by_user_fk
					).first()

					if user_row:
						if current_user_id != added_by_user_fk and current_user_obj.role != RoleModel.ADMIN:
							raise ApplicationError(["resource_not_allowed"])

					# LANGUAGE CODES - START
					lang_en_row = E56_Language.objects.filter(code="en").first()
					lang_en_fk_id = lang_en_row.id

					lang_gr_row = E56_Language.objects.filter(code="gr").first()
					lang_gr_fk_id = lang_gr_row.id

					lang_bg_row = E56_Language.objects.filter(code="bg").first()
					lang_bg_fk_id = lang_bg_row.id

					lang_tk_row = E56_Language.objects.filter(code="tk").first()
					lang_tk_fk_id = lang_tk_row.id
					# LANGUAGE CODES - END

					# TITLE - START
					title_en = req_data.get("title_en", None)

					if title_en:
						E35_Title.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_en_fk_id,
						).update(
							content=title_en,
							ts_added=ts_now,
						)

					title_gr = req_data.get("title_gr", None)

					if title_gr:
						E35_Title.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_gr_fk_id,
						).update(
							content=title_gr,
							ts_added=ts_now,
						)

					title_bg = req_data.get("title_bg", None)

					if title_bg:
						E35_Title.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_bg_fk_id,
						).update(
							content=title_bg,
							ts_added=ts_now,
						)

					title_tk = req_data.get("title_tk", None)

					if title_tk:
						E35_Title.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_tk_fk_id,
						).update(
							content=title_tk,
							ts_added=ts_now,
						)
					# TITLE - END

					# APPELLATION - START
					appellation_en = req_data.get("appellation_en", None)

					if appellation_en:
						E41_Appellation.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_en_fk_id,
						).update(
							content=appellation_en,
							ts_added=ts_now,
						)

					appellation_gr = req_data.get("appellation_gr", None)

					if appellation_gr:
						E41_Appellation.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_gr_fk_id,
						).update(
							content=appellation_gr,
							ts_added=ts_now,
						)

					appellation_bg = req_data.get("appellation_bg", None)

					if appellation_bg:
						E41_Appellation.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_bg_fk_id,
						).update(
							content=appellation_bg,
							ts_added=ts_now,
						)

					appellation_tk = req_data.get("appellation_tk", None)

					if appellation_tk:
						E41_Appellation.objects.filter(
							treasure_fk_id=treasure_uuid,
							language_fk_id=lang_tk_fk_id,
						).update(
							content=appellation_tk,
							ts_added=ts_now,
						)
					# APPELLATION - END

					# EXISTING OBJECT CODE - START
					existing_obj_code = req_data.get("existing_obj_code", None)

					if existing_obj_code:
						E42_Identifier.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							code=existing_obj_code,
							ts_added=ts_now,
						)
					# EXISTING OBJECT CODE - END

					# DESCRIPTION SHORT/EXTENDED - START
					desc_short_version = req_data.get("desc_short_version", None)
					desc_extended_version = req_data.get("desc_extended_version", None)

					if desc_short_version:
						Description.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							short_version=desc_short_version,
							ts_added=ts_now,
						)

					if desc_extended_version:
						Description.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							extended_version=desc_extended_version,
							ts_added=ts_now,
						)
					# DESCRIPTION SHORT/EXTENDED - END

					# TIME SPAN - START
					time_span = req_data.get("time_span", None)

					if time_span:
						E52_Time_Span.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							duration=time_span,
							ts_added=ts_now,
						)
					# TIME SPAN - END

					# KIND - START
					kind = req_data.get("kind", None)

					if kind:
						E55_Type.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							kind=kind,
							ts_added=ts_now,
						)
					# KIND - END

					# CREATOR - START
					creator = req_data.get("creator", None)

					if creator:
						E71_Human_Made_Thing.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							creator=creator,
							ts_added=ts_now,
						)
					# CREATOR - END

					# BEGINNING OF EXISTENCE - START
					beginning_of_existence = req_data.get("beginning_of_existence", None)

					if beginning_of_existence:
						E63_Beginning_of_Existence.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=beginning_of_existence,
							ts_added=ts_now,
						)
					# BEGINNING OF EXISTENCE - END

					# BIOGRAPHY INFORMATION - START 
					was_in_church = req_data.get("was_in_church", None)
					was_in_another_country = req_data.get("was_in_another_country", None)
					was_lost_and_found = req_data.get("was_lost_and_found", None)

					was_in_church_keep_same = False
					was_in_another_country_keep_same = False
					was_lost_and_found_keep_same = False

					biography_row = Biography.objects.filter(
							treasure_fk_id = treasure_uuid,
					).first()

					if was_in_church == "false" or was_in_church == False:
						was_in_church = False
					elif was_in_church == "true" or was_in_church == True:
						was_in_church = True
					else:
						was_in_church = biography_row.was_in_church
						was_in_church_keep_same = True

					if was_in_another_country == "false" or was_in_another_country == False:
						was_in_another_country = False
					elif was_in_another_country == "true" or was_in_another_country == True:
						was_in_another_country = True
					else:
						was_in_another_country = biography_row.was_in_another_country
						was_in_another_country_keep_same = True

					if was_lost_and_found == "false" or was_lost_and_found == False:
						was_lost_and_found = False
					elif was_lost_and_found == "true" or was_lost_and_found == True:
						was_lost_and_found = True
					else:
						was_lost_and_found = biography_row.was_lost_and_found
						was_lost_and_found_keep_same = True

					if not was_in_church_keep_same:
						Biography.objects.filter(
							treasure_fk_id=treasure_uuid
						).update(
							was_in_church=was_in_church,
							ts_added=ts_now,
						)

					if not was_in_another_country_keep_same:
						Biography.objects.filter(
							treasure_fk_id=treasure_uuid
						).update(
							was_in_another_country=was_in_another_country,
							ts_added=ts_now,
						)

					if not was_lost_and_found_keep_same:
						Biography.objects.filter(
							treasure_fk_id=treasure_uuid
						).update(
							was_lost_and_found=was_lost_and_found,
							ts_added=ts_now,
						)
					# BIOGRAPHY INFORMATION - END

					# DIMENSION - START
					dimension = req_data.get("dimension", None)

					if dimension:
						E54_Dimension.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=dimension,
							ts_added=ts_now,
						)
					# DIMENSION - END

					# MATERIAL - START
					material = req_data.get("material", None)

					if material:
						E57_Material.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=material,
							ts_added=ts_now,
						)
					# MATERIAL - END

					# INSCRIPTION - START
					inscription = req_data.get("inscription", None)

					if inscription:
						E34_Inscription.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=inscription,
							ts_added=ts_now,
						)
					# INSCRIPTION - END

					# MANUSCRIPT TEXT - START
					manuscript_text = req_data.get("manuscript_text", None)

					if manuscript_text:
						E73_Information_Object.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=manuscript_text,
							ts_added=ts_now,
						)
					# MANUSCRIPT TEXT - END

					# EVENT INFORMATION - START
					event_information = req_data.get("event_information", None)

					if event_information:
						E5_Event.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=event_information,
							ts_added=ts_now,
						)
					# EVENT INFORMATION - END

					# PREVIOUS DOCUMENTATION - START
					previous_documentation = req_data.get("previous_documentation", None)
					relevant_bibliography = req_data.get("relevant_bibliography", None)

					if previous_documentation:
						Previous_Documentation.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							documentation=previous_documentation,
							ts_added=ts_now,
						)

					if relevant_bibliography:
						Previous_Documentation.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							bibliography=relevant_bibliography,
							ts_added=ts_now,
						)
					# PREVIOUS DOCUMENTATION - END

					# PRESERVATION AND CONSERVATION STATUS - START
					preservation_status = req_data.get("preservation_status", None)
					conservation_status = req_data.get("conservation_status", None)

					if preservation_status:
						E14_Condition_Assessment.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=preservation_status,
							ts_added=ts_now,
						)

					if conservation_status:
						E11_Modification.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=conservation_status,
							ts_added=ts_now,
						)
					# PRESERVATION AND CONSERVATION STATUS - END

					# GROUP OF OBJECTS - START
					group_of_objects = req_data.get("group_of_objects", None)

					if group_of_objects:
						E74_Group.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=group_of_objects,
							ts_added=ts_now,
						)
					# GROUP OF OBJECTS - END

					# COLLECTION IT BELONGS - START
					collection_it_belongs = req_data.get("collection_it_belongs", None)

					if collection_it_belongs:
						E78_Curated_Holding.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=collection_it_belongs,
							ts_added=ts_now,
						)
					# COLLECTION IT BELONGS - END

					# POSITION - START
					position_of_treasure = req_data.get("position_of_treasure", None)

					if position_of_treasure:
						E53_Place.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=position_of_treasure,
							ts_added=ts_now,
						)
					# POSITION - END

					# DATA ADMINISTRATION - START
					people_that_help_with_documentation = req_data.get("people_that_help_with_documentation", None)

					if people_that_help_with_documentation:
						Data_Administration.objects.filter(
							treasure_fk_id=treasure_uuid,
						).update(
							content=people_that_help_with_documentation,
							ts_added=ts_now,
						)
					# DATA ADMINISTRATION - END

				log.info("{} DB LOG".format(request_details(request)),
					extra={
						"user_id": payload["user_id"],
						"api": self.class_name,
						"action": self.class_action,
						"data": model_to_json(req_data),
						"ip_address": get_ip_address(request),
					}
				)
				status_code, message = get_code_and_response(["success"])
				content = {}
				content[MESSAGE] = message
				content[RESOURCE_NAME] = "user"
				response = {}
				response[CONTENT] = content
				response[STATUS_CODE] = status_code
				log.debug("{} SUCCESS".format(request_details(request)))
				data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to update ecclesiastical treasure"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class FileMgmtMediaTempAdd(CreateAPIView):
	"""
	post:
	Creates a new temp media entry based on the file received
	"""
	class_name = "FileMgmtMediaTempAdd"
	class_action = "CREATE"
	serializer_class = TempMediaAddSerializer
	parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
	response_types = [
		["success"],
		["unauthorized"],
		["bad_request"],
		["resource_not_found", "user"],
		["method_not_allowed"],
		["internal_server_error"],
	]
	response_dict = build_fields("FileMgmtMediaTempAdd", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[]
	)
	def post(self, request, *args, **kwargs):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}
			req_data = request.data

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			log.debug("{} START".format(request_details(request)))
			serialized_item = TempMediaAddSerializer(data=req_data)

			if not serialized_item.is_valid():
				log.debug("{} VALIDATION ERROR: {}".format(
						request_details(request),
						serialized_item.formatted_error_response()
					)
				)
				response = {}
				response[CONTENT] = serialized_item.formatted_error_response(include_already_exists=True)
				response[STATUS_CODE] = status.HTTP_400_BAD_REQUEST
				data = response
			else:
				with transaction.atomic():
					try:
						log.debug("{} VALID DATA".format(request_details(request)))

						post = request.POST.copy()
						media_uuid = post.get("media_id")
						media_type = post.get("type")

						post["uuid"] = str(uuid.uuid4())
						post["user_fk"] = payload["user_id"]
						post["media_type"] = media_type
						post["media_type_uuid"] = media_uuid

						user_obj = Users.objects.filter(id=payload["user_id"]).first()

						if not user_obj:
							raise ApplicationError(["resource_not_found", "user"])

						if media_type:
							post["dir_path"] = media_uuid + "/" + hashlib.sha256(str(uuid.uuid4()).encode("utf-8")).hexdigest()
						else:
							post["dir_path"] = hashlib.sha256(str(uuid.uuid4()).encode("utf-8")).hexdigest()

						form = MediaFileForm(post, request.FILES)
						temp_media_item = form.save()
						actual_file_path = DIR_CODE_MEDIA + str(temp_media_item.file_src)

						MediaFile.objects.filter(
							uuid=post["uuid"],
						).update(
							file_src= DIR_MEDIA_TEMP + request.FILES["file_src"].name,
						)

						if os.path.exists(actual_file_path):
							file_extension = pathlib.PurePosixPath(str(temp_media_item.file_src)).suffix
							uuid_file_path = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + post["dir_path"] + "/" + temp_media_item.uuid + file_extension
							tmp_dir_path = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + post["dir_path"]

							if not os.path.exists(tmp_dir_path):
								os.makedirs(tmp_dir_path)

							os.rename(actual_file_path, uuid_file_path)

							MediaFile.objects.filter(
								uuid=post["uuid"],
							).update(
								file_ext=file_extension,
							)

						post["temp_media_item_uuid"] = temp_media_item.uuid
						log.info("{} DB LOG".format(request_details(request)),
							extra={
								"user_id": payload["user_id"],
								"api": self.class_name,
								"action": self.class_action,
								"data": model_to_json(post),
								"ip_address": get_ip_address(request),
							}
						)
						status_code, message = get_code_and_response(["success"])
						content = {}
						content[MESSAGE] = message
						content["resource_obj"] = {
							"uuid": temp_media_item.uuid,
						}

						response = {}
						response[CONTENT] = content
						response[STATUS_CODE] = status_code
						log.debug("{} SUCCESS".format(request_details(request)))
						data = response
					except Exception as e:
						log.debug("{} ERROR: {}".format(request_details(request), str(e)))
						raise
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to create a new temp media entry"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class FileMgmtMediaTempDelete(DestroyAPIView):
	"""
	delete:
	Deletes data of a temp media file based on the `file_id`
	"""
	class_name = "FileMgmtMediaTempDelete"
	class_action = "DELETE"
	response_types = [
		["success"],
		["bad_request"],
		["unauthorized"],
		["resource_not_found", "media_file"],
		["method_not_allowed"],
		["internal_server_error"],
	]
	response_dict = build_fields("FileMgmtMediaTempDelete", response_types)
	parameters = openapi.Parameter(
		"file_id",
		in_=openapi.IN_QUERY,
		description="The uuid of the temp media file you would like to delete",
		type=openapi.TYPE_STRING,
		required=True,
	)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
		manual_parameters=[parameters]
	)
	def delete(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}
			req_data = request.GET

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			log.debug("{} START".format(request_details(request)))
			temp_uuid = req_data.get("file_id")
			user_fk_id = payload["user_id"]
			file_src_to_remove = DIR_MEDIA_TEMP + temp_uuid

			dir_to_remove = ""
			is_to_delete = False

			with transaction.atomic():
				instance = MediaFile.objects.filter(
					file_src = file_src_to_remove,
					user_fk_id = user_fk_id
				).first()

				if instance:
					dir_to_remove = DIR_CODE_MEDIA + DIR_MEDIA_TEMP + str(instance.dir_path)
					instance.delete()
					is_to_delete = True
				else:
					log.debug("{} Media file not found.".format(request_details(request)))
					raise ApplicationError(["resource_not_found", "media_file"])

			if is_to_delete:
				try:
					shutil.rmtree(dir_to_remove)
					log.debug("{} Temp media deleted: {}".format(request_details(request), dir_to_remove))
				except Exception as e:
					log.debug("{} Temp media cannot be deleted. Error: {}".format(request_details(request), str(e)))

			log.info("{} DB LOG".format(request_details(request)),
				extra={
					"user_id": payload["user_id"],
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"ip_address": get_ip_address(request),
				}
			)
			status_code, message = get_code_and_response(["success"])
			content = {}
			content[MESSAGE] = message
			content[RESOURCE_NAME] = "media_file"
			response = {}
			response[CONTENT] = content
			response[STATUS_CODE] = status_code
			log.debug("{} SUCCESS".format(request_details(request)))
			data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"data": model_to_json(req_data),
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to delete temp media entry"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])


class SystemLogsList(GenericAPIView):
	"""
	get:
	Returns the list of all system logs
	"""
	class_name = "SystemLogsList"
	class_action = "LIST"
	response_types = [
		["success"],
		["unauthorized"],
		["resource_not_allowed"],
		["method_not_allowed"],
		["unsupported_media_type"],
		["internal_server_error"]
	]
	response_dict = build_fields("SystemLogsList", response_types)

	@swagger_auto_schema(
		responses=response_dict,
		security=[],
	)
	def get(self, request):
		try:
			log.debug("{} Received request".format(request_details(request)))
			response = {}
			data = {}

			is_valid, payload = at.authenticate(request)

			if not is_valid:
				raise ApplicationError(["unauthorized"])

			log.debug("{} VALID DATA".format(request_details(request)))

			current_user_obj = Users.objects.filter(id=payload["user_id"]).first()

			if current_user_obj.role != RoleModel.ADMIN:
				raise ApplicationError(["resource_not_allowed"])

			list_results = list(LoggingEntries.objects.all().values())

			log.info("{} DB LOG".format(request_details(request)),
				extra={
					"user_id": payload["user_id"],
					"api": self.class_name,
					"action": self.class_action,
					"ip_address": get_ip_address(request),
				}
			)

			status_code, message = get_code_and_response(["success"])
			content = {}
			content[MESSAGE] = message
			content[RESOURCE_ARRAY] = list_results
			response = {}
			response[CONTENT] = content
			response[STATUS_CODE] = status_code
			log.debug("{} SUCCESS".format(request_details(request)))
			data = response
		except ApplicationError as e:
			log.info("{} DB LOG (ApplicationError): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			response = {}
			response[CONTENT] = e.get_response_body()
			response[STATUS_CODE] = e.status_code
			data = response
		except Exception as e:
			log.error("{} DB LOG (Internal error): {}".format(request_details(request), str(e)),
				extra={
					"api": self.class_name,
					"action": self.class_action,
					"error_data": str(e),
					"ip_address": get_ip_address(request),
					"is_error": True
				}
			)
			status_code, _ = get_code_and_response(["internal_server_error"])
			content = {
				MESSAGE: "Unable to list system logs"
			}
			return Response(content, status=status_code)

		return Response(data[CONTENT], status=data[STATUS_CODE])
