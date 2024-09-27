from django import forms
from django.forms import ModelForm
from .models import *


class MediaFileForm(ModelForm):
	user = forms.IntegerField(required=False)
	treasure = forms.IntegerField(required=False)
	media_type = forms.CharField(required=False)
	media_type_uuid = forms.CharField(required=False)
	is_file_synced = forms.BooleanField(required=False)
	ts_synced = forms.DateTimeField(required=False)
	ts_added = forms.DateTimeField(required=False)
	file_ext = forms.CharField(required=False)

	class Meta:
		model = MediaFile
		fields = "__all__"
