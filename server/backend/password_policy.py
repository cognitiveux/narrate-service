PASSWORD_POLICY_OPTIONS = {
	"minLength": 8,
}


def is_compliant(password):
	if len(password) < PASSWORD_POLICY_OPTIONS["minLength"]:
		return False

	return True
