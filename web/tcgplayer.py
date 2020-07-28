import json
import requests
from web import config

CATEGORY = 1  # Magic the Gathering
PAGE_LENGTH = 100  # API's max items per page limit is 100


class TCGPlayerException(Exception):
	pass


class NoResults(TCGPlayerException):
	pass


def _send(
	method: str,
	endpoint: str,
	params: any = None,
	data: any = None,
	token: str = None
) -> any:
	"""Send a request to the TCGplayer API.

	:param method: HTTP method to use
	:type method: str
	:param endpoint: API endpoint to send request to
	:type endpoint: str
	:param params: URL parameters, defaults to None
	:type params: any, optional
	:param data: Request data, defaults to None
	:type data: any, optional
	:param token: Bearer token, defaults to None
	:type token: str, optional
	:raises TCGPlayerException: An HTTP error occurred
	:return: The response returned, decoded into an object
	:rtype: any
	"""
	headers = {}
	if token:
		headers['Authorization'] = f'bearer {token}'

	response = requests.request(
		method,
		f'https://api.tcgplayer.com{endpoint}',
		headers=headers,
		params=params,
		data=data
	)
	try:
		response.raise_for_status()
	except requests.HTTPError as e:
		code = e.response.status_code
		if code == 404:
			raise NoResults from e

		raise TCGPlayerException from e

	resp = json.loads(response.text)
	return resp


def _get(endpoint, **kwargs):
	"""Wrapper function for sending GET requests."""
	return _send('GET', endpoint, **kwargs)


def _post(endpoint, **kwargs):
	"""Wrapper function for sending POST requests."""
	return _send('POST', endpoint, **kwargs)


def login() -> str:
	data = {
		'grant_type': 'client_credentials',
		'client_id': config.TCGPLAYER_PUBLICKEY,
		'client_secret': config.TCGPLAYER_PRIVATEKEY
	}
	token = _post(
		'/token',
		data=data
	)['access_token']

	return token


def _offset(page):
	"""Convert a page number into an offset."""
	return (page - 1) * PAGE_LENGTH


def _all_pages(callback, **kwargs):
	"""Get all pages available for a given endpoint.

	:param callback: Callback function getting the pages
	:type callback: function
	"""
	page = 1
	results = []
	token = login()
	while True:
		try:
			resp = callback(page, token, **kwargs)
		except NoResults:
			# 404, meaning no more results
			break

		if len(resp) == 0:
			# Backup to prevent infinite loop, in case API stops 404-ing
			break

		results += resp
		page += 1

	return results


def get_groups(page, token):
	params = {
		'offset': _offset(page),
		'limit': PAGE_LENGTH,
	}
	resp = _get(
		f'/catalog/categories/{CATEGORY}/groups',
		params=params,
		token=token
	)

	groups = resp['results']
	return groups


def get_all_groups():
	return _all_pages(get_groups)


def get_products(page, token, groupid=None):
	params = {
		'productTypes': 'Cards',
		'categoryId': CATEGORY,  # Only MTG cards
		'groupid': groupid,
		'offset': _offset(page),
		'limit': PAGE_LENGTH,
		'getExtendedFields': True
	}
	resp = _get(
		'/catalog/products',
		params=params,
		token=token
	)

	products = resp['results']
	for p in products:
		# Convert extended data to dictionary
		extras = {}
		for data in p['extendedData']:
			extras[data['name']] = data['value']
		p['extendedData'] = extras
	return products


def get_all_products(groupid):
	return _all_pages(get_products, groupid=groupid)


def get_product_prices(products):
	productids = ','.join([str(p) for p in products])
	token = login()
	return _get(f'/pricing/product/{productids}', token=token)['results']
