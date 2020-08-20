from functools import wraps
from flask import request, jsonify
from flasktools import params_to_dict
from flasktools.db import fetch_query


def paginated(f):
	"""Parse pagination URL parameters, and pass them through to function.

	Will pass through page & limit as the first 2 parameters."""
	DEFAULT_LIMIT = 250
	MAX_LIMIT = 2500

	@wraps(f)
	def decorated_function(*args, **kwargs):
		params = params_to_dict(request.args)
		page = params.get('page') or 1
		limit = params.get('limit') or DEFAULT_LIMIT
		limit = max(limit, MAX_LIMIT)

		try:
			limit = int(params.get('limit'))
		except (TypeError, ValueError):
			# raise
			limit = DEFAULT_LIMIT

		return f(page, limit, *args, **kwargs)

	return decorated_function


def auth_required(f):
	"""Validate the API key provided in the request headers."""
	def validate(apikey):
		"""Check if a user exists with this API key."""
		user = fetch_query(
			"SELECT id FROM user_account WHERE apikey = %(apikey)s",
			{'apikey': apikey},
			single_row=True
		)
		return user

	@wraps(f)
	def decorated_function(*args, **kwargs):
		apikey = request.headers.get('X-API-KEY')
		if not apikey:
			return jsonify(error='Missing API Key'), 400
		if not validate(apikey):
			return jsonify(error='Invalid API Key'), 401

		return f(*args, **kwargs)

	return decorated_function
