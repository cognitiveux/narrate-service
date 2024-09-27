from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.timezone import now
from django.core.files.storage import FileSystemStorage
from datetime import timedelta

upload_protected_storage = FileSystemStorage(location=settings.PROTECTED_MEDIA_ROOT)


class OrganizationModel(models.Model):
	AUTH = "AUTH"
	IHU = "IHU"
	KMKD = "KMKD"
	SUSKO = "SUSKO"
	OTHER = "Other / Not listed"

	ORGANIZATION_CHOICES = (
		(AUTH, "AUTH"),
		(IHU, "IHU"),
		(KMKD, "KMKD"),
		(SUSKO, "SUSKO"),
		(OTHER, "Other / Not listed"),
	)


class RoleModel(models.Model):
	ADMIN = "ADMIN"
	REGULAR = "REGULAR"

	ROLE_CHOICES = (
		(ADMIN, "ADMIN"),
		(REGULAR, "REGULAR"),
	)


class Users(AbstractBaseUser):
	email = models.EmailField(max_length=100, unique=True)
	name = models.CharField(max_length=500)
	organization = models.CharField(max_length=50, choices=OrganizationModel.ORGANIZATION_CHOICES)
	password = models.CharField(max_length=500)
	role = models.CharField(max_length=7, null=False, blank=False, default=RoleModel.REGULAR)
	surname = models.CharField(max_length=500)
	telephone = models.CharField(max_length=100, null=True, blank=True, default="")
	file_src = models.CharField(max_length=1000, null=True, blank=True, default="/static/backend/assets/media/blank.png")
	c_register_task_id = models.CharField(max_length=100, default="")
	c_reset_task_id = models.CharField(max_length=100, default="")
	ts_registration = models.DateTimeField(default=now)

	USERNAME_FIELD = "email"


class Ecclesiastical_Treasures(models.Model):
	uuid = models.CharField(max_length=100, unique=True, null=False)
	user_fk = models.ForeignKey(
		Users,
		to_field="id",
		on_delete=models.CASCADE,
	)
	ref_code = models.CharField(max_length=100, null=True, blank=True)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E56_Language(models.Model):
	code = models.CharField(max_length=1000, unique=True, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E5_Event(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E11_Modification(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E14_Condition_Assessment(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E34_Inscription(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E35_Title(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	language_fk = models.ForeignKey(
		E56_Language,
		on_delete=models.CASCADE,
		to_field="id"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E41_Appellation(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	language_fk = models.ForeignKey(
		E56_Language,
		on_delete=models.CASCADE,
		to_field="id"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E42_Identifier(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	code = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E52_Time_Span(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	duration = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E53_Place(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E54_Dimension(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E55_Type(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	kind = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E57_Material(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E63_Beginning_of_Existence(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E71_Human_Made_Thing(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	creator = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E73_Information_Object(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E74_Group(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.JSONField(default=None)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class E78_Curated_Holding(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.CharField(max_length=1000, null=False, blank=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Biography(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	was_in_church = models.BooleanField(default=False)
	was_in_another_country = models.BooleanField(default=False)
	was_lost_and_found = models.BooleanField(default=False)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Data_Administration(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	content = models.JSONField(default=None)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Description(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	short_version = models.CharField(max_length=1000, null=True, blank=True, default=None)
	extended_version = models.CharField(max_length=10000, null=True, blank=True, default=None)
	user_role = models.CharField(max_length=20, default=RoleModel.REGULAR)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Pieces_of_Ecclesiastical_Treasure(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	documentation = models.CharField(max_length=1000, null=True, blank=True, default=None)
	bibliography = models.CharField(max_length=1000, null=True, blank=True , default=None)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Previous_Documentation(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	documentation = models.CharField(max_length=1000, null=True, blank=True, default=None)
	bibliography = models.CharField(max_length=1000, null=True, blank=True , default=None)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class Treasure_Images(models.Model):
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		on_delete=models.CASCADE,
		to_field="uuid"
	)
	file_src = models.CharField(max_length=1000, null=True, blank=True, default=None)
	order = models.IntegerField(default=1)
	ts_added = models.DateTimeField(default=now)
	ts_updated = models.DateTimeField(default=now)


class MediaFile(models.Model):
	uuid = models.CharField(max_length=100, unique=True, null=False)
	user_fk = models.ForeignKey(
		Users,
		to_field="id",
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		default=None,
	)
	treasure_fk = models.ForeignKey(
		Ecclesiastical_Treasures,
		to_field="uuid",
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		default=None,
	)
	media_type = models.CharField(max_length=100, null=True, default="")
	media_type_uuid = models.CharField(max_length=100, null=True, default="")
	dir_path = models.CharField(max_length=500, null=False)
	file_src = models.FileField(upload_to="media/temporary", storage=upload_protected_storage)
	file_ext = models.CharField(max_length=100, null=True, default="")
	is_file_synced = models.BooleanField(default=False)
	ts_synced = models.DateTimeField(null=True, default=None)
	ts_added = models.DateTimeField(default=now)


class ResetPassword(models.Model):
	def calculate_expiration():
		return now() + timedelta(seconds=settings.RESET_PASSWORD_INTERVAL)

	user_fk = models.ForeignKey(
		Users,
		on_delete=models.CASCADE
	)
	frequent_request_count = models.IntegerField(default=0)
	reset_code = models.CharField(max_length=50)
	ts_expiration_reset = models.DateTimeField(null=True, default=calculate_expiration)
	ts_reset = models.DateTimeField(null=True)
	ts_requested = models.DateTimeField(default=now)


class ActiveUsers(models.Model):
	user_fk = models.ForeignKey(
		Users,
		on_delete=models.CASCADE,
	)
	activation_code = models.CharField(max_length=50)
	frequent_request_count = models.IntegerField(default=0)
	ts_activation = models.DateTimeField(null=True, default=None)
	ts_added = models.DateTimeField(default=now)


class LoggingEntries(models.Model):
	user_fk = models.ForeignKey(
		Users,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		default=None,
	)
	api = models.CharField(max_length=100, null=True, blank=True, default=None)
	action = models.CharField(max_length=100, null=True, blank=True, default=None)
	data = models.TextField(max_length=1000, null=True, blank=True, default=None)
	error_data = models.TextField(max_length=1000, null=True, blank=True, default=None)
	ip_address = models.CharField(max_length=100, null=True, blank=True, default=None)
	is_error = models.BooleanField(null=True, blank=True, default=False)
	ts_added = models.DateTimeField(default=now)
	ts_last_updated = models.DateTimeField(default=now)
