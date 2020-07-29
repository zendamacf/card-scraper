from functools import wraps
from flask import request
from flasktools import params_to_dict


def paginated(f):
	"""Parse pagination URL parameters, and pass them through to function.

	Will pass through page & limit as the first 2 parameters."""
	DEFAULT_LIMIT = 250

	@wraps(f)
	def decorated_function(*args, **kwargs):
		params = params_to_dict(request.args)
		page = params.get('page') or 1
		limit = params.get('limit') or DEFAULT_LIMIT

		try:
			limit = int(params.get('limit'))
		except (TypeError, ValueError):
			# raise
			limit = DEFAULT_LIMIT

		return f(page, limit, *args, **kwargs)

	return decorated_function
