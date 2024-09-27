from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import views

schema_view = get_schema_view(
	openapi.Info(
		title="NARRATE API",
		default_version="v2",
		description="The endpoints for interacting with the NARRATE service",
		contact=openapi.Contact(email="YOUR_EMAIL@DOMAIN.COM"),
		license=openapi.License(name="GNU General Public License v3.0"),
	),
	public=True,
	permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
	re_path(r"^demo(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
	re_path(r"^demo/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
	re_path(r"^doc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
	re_path(r"^protected_media/(?P<path>.*)$", views.protected_media, name="protected_media"),

	# Account Management/Actions
	re_path(r"^account-management/activate_account/$", views.ActivateAccount.as_view(), name="account-management/activate_account"),
	re_path(r"^account-management/login/$", views.Login.as_view(), name="account-management/login"),
	re_path(r"^account-management/poll_reset_email_status/$", views.PollResetEmailStatus.as_view(), name="account-management/poll_reset_email_status"),
	re_path(r"^account-management/refresh_token/$", views.RefreshToken.as_view(), name="account-management/refresh_token"),
	re_path(r"^account-management/register_user/$", views.RegisterUser.as_view(), name="account-management/register_user"),
	re_path(r"^account-management/request_password_reset_code/$", views.RequestPasswordResetCode.as_view(), name="account-management/request_password_reset_code"),
	re_path(r"^account-management/reset_password/$", views.ResetAccountPassword.as_view(), name="account-management/reset_password"),
	re_path(r"^account-management/update_password/$", views.UpdatePassword.as_view(), name="account-management/update_password"),
	re_path(r"^account-management/update_profile/$", views.UpdateProfile.as_view(), name="account-management/update_profile"),
	re_path(r"^activate_account/$", views.activateAccountView, name="activate_account"),
	re_path(r"^forgot_password/$", views.forgotPasswordView, name="forgot_password"),
	re_path(r"^kr/$", views.knowledgeRepositoryView, name="kr"),
	re_path(r"^login/$", views.loginView, name="login"),
	re_path(r"^logout/$", views.logout, name="logout"),
	re_path(r"^no_permission/?$", views.noPermissionView, name="no_permission"),
	re_path(r"^profile/$", views.profileView, name="profile"),
	re_path(r"^reset_password/$", views.resetPasswordView, name="reset_password"),
	re_path(r"^security/$", views.securityView, name="security"),
	re_path(r"^sign_up/$", views.signUpView, name="sign_up"),

	# Dashboard and Ecclesiastical Treasures Management/Actions
	re_path(r"^dashboard/$", views.dashboardView, name="dashboard"),
	re_path(r"^ecclesiastical-treasures/create/$", views.EcclesiasticalTreasuresCreate.as_view(), name="ecclesiastical-treasures/create"),
	re_path(r"^ecclesiastical-treasures/delete/$", views.EcclesiasticalTreasuresDelete.as_view(), name="ecclesiastical-treasures/delete"),
	re_path(r"^ecclesiastical-treasures/fetch/$", views.EcclesiasticalTreasuresFetch.as_view(), name="ecclesiastical-treasures/fetch"),
	re_path(r"^ecclesiastical-treasures/list/$", views.EcclesiasticalTreasuresList.as_view(), name="ecclesiastical-treasures/list"),	
	re_path(r"^ecclesiastical-treasures/media/delete/$", views.EcclesiasticalTreasuresMediaDelete.as_view(), name="ecclesiastical-treasures/media/delete"),
	re_path(r"^ecclesiastical-treasures/media/list/$", views.EcclesiasticalTreasuresMediaList.as_view(), name="ecclesiastical-treasures/media/list"),
	re_path(r"^ecclesiastical-treasures/media/update/$", views.EcclesiasticalTreasuresMediaUpdate.as_view(), name="ecclesiastical-treasures/media/update"),
	re_path(r"^ecclesiastical-treasures/media/upload_new/$", views.EcclesiasticalTreasuresMediaUploadNew.as_view(), name="ecclesiastical-treasures/media/upload_new"),
	re_path(r"^ecclesiastical-treasures/update/$", views.EcclesiasticalTreasuresUpdate.as_view(), name="ecclesiastical-treasures/update"),
	re_path(r"^treasures/add/$", views.treasuresAddView, name="treasures/add"),
	re_path(r"^treasures/delete/$", views.treasuresDeleteView, name="treasures/delete"),
	re_path(r"^treasures/media/$", views.treasuresMediaView, name="treasures/media"),
	re_path(r"^treasures/media/add/$", views.treasuresMediaAddView, name="treasures/media/add"),
	re_path(r"^treasures/media/delete/$", views.treasuresMediaDeleteView, name="treasures/media/delete"),
	re_path(r"^treasures/media/update/$", views.treasuresMediaUpdateView, name="treasures/media/update"),
	re_path(r"^treasures/update/$", views.treasuresUpdateView, name="treasures/update"),
	re_path(r"^treasures/view/$", views.treasuresView, name="treasures/view"),

	# File Management
	re_path(r"^file-management/media/temp/add/$", views.FileMgmtMediaTempAdd.as_view(), name="file-management/media/temp/add"),
	re_path(r"^file-management/media/temp/delete/$", views.FileMgmtMediaTempDelete.as_view(), name="file-management/media/temp/delete"),

	# System Logs
	re_path(r"^system-logs/list/$", views.SystemLogsList.as_view(), name="system-logs/list"),

	re_path(r"^$", views.dashboardView, name="dashboard"),
]

if settings.DEBUG is True:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
