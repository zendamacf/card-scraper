from web import app, config, tcgplayer
from flasktools import params_to_dict
from flasktools.celery import setup_celery
from flasktools.db import mutate_query
import rollbar
from celery.signals import task_failure

celery = setup_celery(app)
QUEUE = 'cardscraper'


@task_failure.connect
def handle_task_failure(**kwargs):
	if not hasattr(config, 'TESTMODE'):
		env = 'production' if not hasattr(config, 'TESTMODE') else 'development'
		rollbar.init(
			config.ROLLBAR_TOKEN,
			environment=env
		)

		def celery_base_data_hook(request, data):
			data['framework'] = 'celery'

		rollbar.BASE_DATA_HOOK = celery_base_data_hook

		rollbar.report_exc_info(extra_data=kwargs)


@celery.task(queue=QUEUE)
def fetch_cards(groupid: int, name: str) -> None:
	"""Fetch cards from TCGplayer and store them in the database.

	:param groupid: TCGplayer group ID for this set
	:type groupid: int
	:param name: The name of the set
	:type name: str
	"""
	print(f'[{name}]: Fetching cards')
	products = []
	for r in tcgplayer.get_all_products(groupid):
		if r['extendedData']['Rarity'] not in ['T']:  # Ignore tokens
			products.append(_map_card(r))

	_insert_cards(products)
	print(f'[{name}]: Updated {len(products)} cards')


@celery.task(queue=QUEUE)
def fetch_prices(cards: list) -> None:
	"""Fetch card prices from TCGplayer and store them in the database.

	:param cards: The list of TCGplayer product IDs of the cards to check
	:type cards: list
	"""
	print(f'Getting prices for {len(cards)} cards')
	prices = tcgplayer.get_product_prices([c['tcgplayerid'] for c in cards])

	inserts = []
	for p in prices:
		if p['lowPrice'] or p['midPrice'] or p['highPrice'] or p['marketPrice']:
			inserts.append(p)
	print(f'Got {len(inserts)}/{len(prices)} prices to add')

	mutate_query(
		"""
		INSERT INTO price (cardid, low, mid, high, market, foil)
		SELECT
			id,
			%(lowPrice)s,
			%(midPrice)s,
			%(highPrice)s,
			%(marketPrice)s,
			%(subTypeName)s = 'Foil'
		FROM card WHERE tcgplayerid = %(productId)s
		ON CONFLICT (cardid, foil, created) DO NOTHING;
		""",
		inserts,
		executemany=True
	)
	print(f'Updated {len(inserts)} prices for {len(cards)} cards')


def _strip_newlines(s):
	"""Strip newline characters from a string."""
	if s is not None:
		s = s.replace('\n', '').replace('\r', '')
	return s


def _map_card(product):
	"""Map TCGplayer product to object closer matching our DB schema."""
	# Strip whitespace & convert empty strings to None
	product = params_to_dict(product)

	return {
		'id': product['productId'],
		'name': product['name'],
		'groupid': product['groupId'],
		'collectornumber': product['extendedData'].get('Number'),
		'rarity': product['extendedData']['Rarity'],
		'type': product['extendedData'].get('SubType'),
		'power': product['extendedData'].get('P'),
		'toughness': product['extendedData'].get('T'),
		'oracle': _strip_newlines(product['extendedData'].get('OracleText')),
		'flavor': _strip_newlines(product['extendedData'].get('FlavorText')),
		'url': product['url'],
		# Increase the image resolution
		'imageurl': product['imageUrl'].replace('200w', '400w')
	}


def _insert_cards(products):
	"""Insert a list of products to the database."""
	mutate_query(
		"""
		INSERT INTO card (
			tcgplayerid,
			name,
			card_setid,
			collectornumber,
			rarity,
			type,
			power,
			toughness,
			oracletext,
			flavortext,
			url,
			imageurl
		) SELECT
			%(id)s,
			%(name)s,
			(SELECT id FROM card_set WHERE tcgplayerid = %(groupid)s),
			%(collectornumber)s,
			%(rarity)s,
			%(type)s,
			%(power)s,
			%(toughness)s,
			%(oracle)s,
			%(flavor)s,
			%(url)s,
			%(imageurl)s
		WHERE NOT EXISTS (SELECT 1 FROM card WHERE tcgplayerid = %(id)s)
		""",
		products,
		executemany=True
	)
