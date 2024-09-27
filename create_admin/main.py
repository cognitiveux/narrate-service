import psycopg2
import random
import string
import uuid

from datetime import datetime
from django.conf import settings
from django.contrib.auth.hashers import make_password

# Required for password hashes
settings.configure()


def get_random_string(length):
	return "".join(random.choice(string.ascii_letters) for i in range(length))


def generate_activation_code():
	return uuid.uuid4().hex[0:6]


def insert_admin_user(conn, cursor):
	ts_now =  datetime.now()

	try:
		email = "admin@narrate.com"
		name = "Admin"
		organization = "Other / Not listed"
		password = get_random_string(12)
		password_hash = make_password(password)
		role = "ADMIN"
		surname = "Admin"
		telephone = ""
		c_register_task_id = "test_register_task_id"
		c_reset_task_id = "test_reset_task_id"
		file_src = "/static/backend/assets/media/blank.png"

		cursor.execute("INSERT INTO public.backend_users ( \
			email, name, organization, password, \
				role, surname, telephone, file_src, c_register_task_id, c_reset_task_id, ts_registration) \
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
			(
				email, name, organization, password_hash,
				role, surname, telephone, file_src, c_register_task_id, c_reset_task_id, ts_now,
			)
		)

		# Get the ID of the newly created admin user account
		cursor.execute("SELECT id FROM public.backend_users WHERE email = %s", (email,))
		user_id = None

		for i, record in enumerate(cursor):
			user_id = record[0]
			break

		activation_code = generate_activation_code()

		# Update activated users accounts for the admin user account
		cursor.execute("INSERT INTO public.backend_activeusers ( \
			user_fk_id, activation_code, frequent_request_count, ts_activation, ts_added) \
			VALUES (%s, %s, %s, %s, %s)",
			(
				user_id, activation_code, 1, ts_now, ts_now, 
			)
		)

		conn.commit()
		print("email: {}\npassword: {}\norganization: {}".format(email, password, organization))
	except Exception as e:
		print("[insert_admin_user] Error occurred: {}".format(str(e)))


def run():
	try:
		conn = psycopg2.connect("dbname=postgres user=postgres host=narrate-postgres")
		cursor = conn.cursor()
		insert_admin_user(conn, cursor)
		cursor.close()
		conn.close()
	except Exception as e:
		print("Error occurred: {}".format(str(e)))


if __name__ == "__main__":
	run()
