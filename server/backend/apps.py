from django.apps import AppConfig

class NarrateAppConfig(AppConfig):
	name = "backend"

	def ready(self):
		from django.apps import apps

		E56_Language = apps.get_model("backend", "E56_Language")
		try:
			# Populate language codes
			E56_Language.objects.get_or_create(code="en")
			E56_Language.objects.get_or_create(code="gr")
			E56_Language.objects.get_or_create(code="bg")
			E56_Language.objects.get_or_create(code="tk")
		except Exception as e:
			print("Error occured during populating db data: {}".format(str(e)))
			pass
