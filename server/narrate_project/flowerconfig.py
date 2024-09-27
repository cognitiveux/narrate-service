import json
import os

def format_task(task):
	task.args = ""
	return task

basic_auth = [os.environ["FLOWER_USER"] + ":" + os.environ["FLOWER_PASSWORD"]]
