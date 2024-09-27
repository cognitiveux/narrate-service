from django.conf import settings
import inspect
import logging
import sys

from backend.models import (
	LoggingEntries,
	Users,
)


class DatabaseLogHandler(logging.Handler):
	def emit(self, record):
		try:
			user = Users.objects.get(id=record.user_id) if hasattr(record, "user_id") and record.user_id else None
			log_entry = LoggingEntries(
				user_fk_id=user.id if user else None,
				api=getattr(record, "api", None),
				action=getattr(record, "action", None),
				data=getattr(record, "data", None),
				error_data=getattr(record, "error_data", None),
				ip_address=getattr(record, "ip_address", None),
				is_error=getattr(record, "is_error", False),
			)
			log_entry.save()
		except Exception as e:
			print("Failed to save log to database. Reason: {}".format(str(e)))


class ClassFilter(logging.Filter):
	def _get_class_from_frame(self,fr):
		args, _, _, value_dict = inspect.getargvalues(fr)
		instance = None

		if len(args) and args[0] == "self":
			instance = value_dict.get("self", None)

		if instance:
			return getattr(instance, "__class__", None)

		return None

	def filter(self, record):
		stack = inspect.stack()
		unwanted_classes = ["Logger", "ClassFilter"]

		for stack_frame in stack:
			class_obj = self._get_class_from_frame(stack_frame[0])

			if class_obj and class_obj.__name__ not in unwanted_classes:
				if class_obj:
					classname = class_obj.__name__
				else:
					classname = "None"
				break

		record.classname = classname
		return True


logger = logging.getLogger("narrate_logger")
logger.setLevel(logging.DEBUG)
logger.addFilter(ClassFilter())

fh = logging.FileHandler(settings.LOGGER_PATH)
fh.setLevel(logging.DEBUG)

db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s - %(classname)s - %(funcName)s - %(asctime)s - %(message)s")
fh.setFormatter(formatter)
db_handler.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(db_handler)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)
