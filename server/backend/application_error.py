from .status_codes import *


class ApplicationError(Exception):
	def __init__(self, status_list=None, status_code=None, message=None, **kwargs):
		self._response_body = {}

		if len(status_list)>=2:
			if status_list[1] in RESOURCE_NAMES:
				self._response_body["resource_name"] = status_list[1]
			elif status_list[0] in VARIABLE_RESULTS:
				self._response_body["resource"] = status_list[1]

		for key,value in kwargs.items():
			self._response_body[key] = value

		if status_code or message:
			self.status_code = status_code
			self.message = message
			return

		status_dict = build_response_dictionary([status_list], is_description=False)

		if status_list[0] in STATUS_CODES.keys():
			self.status_code = STATUS_CODES[status_list[0]]["code"]
		else:
			self.status_code = VARIABLE_RESULTS[status_list[0]]["code"]

		self.message = status_dict[self.status_code]

	def get_response_body(self):
		self._response_body["message"] = self.message
		return self._response_body
