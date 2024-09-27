import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "narrate_project.settings")

app = Celery("narrate_project", backend="amqp", broker="amqp://rabbitmq:rabbitmq@narrate-rabbit:5672")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
	print("Request: {0!r}".format(self.request))
