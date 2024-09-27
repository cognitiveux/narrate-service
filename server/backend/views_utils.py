from datetime import date
from django.conf import settings
from django.core.serializers import serialize
from django.db import models
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from .custom_logging import logger as log

import json
import smtplib
import ssl
import uuid


EMAIL_BODY =  """
Hi,\n\nTo activate your account, please use the following activation code:{} \nby visiting the following url: {}\n\n
If you did not request this code, please let us know.\n\nThanks,\nNARRATE Team
"""

EMAIL_HTML = """
<html>
	<body>
		<p>Hi,<br><br>
			To activate your account, please use the following activation code:<br><br>
			<strong>{}</strong><br><br>
			by visiting the following url:<br><br>
			<strong>{}</strong><br>
		</p>
		<p>If you did not request this code, please let us know.</p><br><br>
		<p>Thanks,<br>
		NARRATE Team</p>
	</body>
</html>
"""

EMAIL_BODY_RESET_PASSWORD = """
Hi,\n\nTo reset your password, please use the following code:{} \nby visiting the following url: {}\n\n
If you did not request this code, please let us know.\n\nThanks,\nNARRATE Team
"""

EMAIL_HTML_RESET_PASSWORD ="""
<html>
	<body>
		<p>Hi,<br><br>
			To reset your password, please use the following code:<br><br>
			<strong>{}</strong><br><br>
			by visiting the following url:<br><br>
			<strong>{}</strong><br>
		</p>
		<p>If you did not request this code, please let us know.</p><br><br>
		<p>Thanks,<br>
		NARRATE Team</p>
	</body>
</html>
"""

class DateEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, date):
			return obj.isoformat()

		return super(DateEncoder, self).default(obj)


def generate_random_uuid():
	return uuid.uuid4().hex


def request_details(request):
	username = None

	if isinstance(request, dict):
		user = request.get("user")
		if user:
			username =  user.get("username")
		else:
			username = request["data"].get("username")
	else:
		try:
			username = request.user.email or request.data.get("email")
		except AttributeError as e:
			username = None

	if not username:
		username = "anonymous"

	return get_ip_address(request)+" - "+username+" - "


def get_ip_address(request):
	ip = None

	if isinstance(request, dict):
		x_forwarded_for = request["META"]["HTTP_X_FORWARDED_FOR"]

		if x_forwarded_for:
			ip = x_forwarded_for.split(",")[0]
		else:
			ip = request["META"]["REMOTE_ADDR"]
	else:
		x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

		if x_forwarded_for:
			ip = x_forwarded_for.split(",")[0]
		else:
			ip = request.META.get("REMOTE_ADDR")

	return ip


def build_email_object(fromaddr, toaddr, code=None, reset_password_url=None):
	msg = MIMEMultipart("alternative")
	msg["From"] = fromaddr
	msg["To"] = toaddr

	if reset_password_url:
		msg["Subject"] = "NARRATE - Reset Password"
		text = EMAIL_BODY_RESET_PASSWORD.format(code, reset_password_url)
		html = EMAIL_HTML_RESET_PASSWORD.format(code, reset_password_url)
	else:
		activate_account_url = settings.ACTIVATE_ACCOUNT_BASE_URL
		msg["Subject"] = "NARRATE - Activate Account"
		text = EMAIL_BODY.format(code, activate_account_url)
		html = EMAIL_HTML.format(code, activate_account_url)

	part1 = MIMEText(text, "plain")
	part2 = MIMEText(html, "html")
	msg.attach(part1)
	msg.attach(part2)

	return msg


def send_email(email, code=None, reset_password_url=None):
	function_name = "send_email"
	function_action = "CREATE"
	log.debug("Will send email to address: {}".format(email))
	fromaddr = settings.GLOBAL_SETTINGS.get("FROM_EMAIL")
	fromaddr_alias = settings.GLOBAL_SETTINGS.get("FROM_EMAIL_ALIAS")
	toaddr = email
	password = settings.GLOBAL_SETTINGS.get("EMAIL_PASSWORD")
	msg = build_email_object(fromaddr_alias, toaddr, code, reset_password_url)
	req_obj = {
		"email": email,
		"code": code,
		"reset_password_url": reset_password_url,
	}

	try:
		context = ssl.create_default_context()

		with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
			server.login(fromaddr, password)
			server.sendmail(
				fromaddr, toaddr, msg.as_string()
			)
			log.info("DB LOG. Email sent to address: {}".format(email),
				extra={
					"api": function_name,
					"action": function_action,
					"data": model_to_json(req_obj),
				}
			)
	except Exception as e:
		log.error("DB LOG (Internal error). email: {}. Reason: {}".format(email, str(e)),
			extra={
				"api": function_name,
				"action": function_action,
				"data": model_to_json(req_obj),
				"error_data": str(e),
				"is_error": True
			}
		)
		raise


def model_to_json(instance):
	json_data = ""
	try:
		if isinstance(instance, models.Model):
			json_data = serialize("json", [instance])
			return json_data
		elif isinstance(instance, dict):
			json_data = instance
	except Exception as e:
		json_data = ""

	return json.dumps(json_data, cls=DateEncoder)
