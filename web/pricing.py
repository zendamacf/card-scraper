from flask import Blueprint, jsonify
from flasktools.db import fetch_query
from web import asynchro


bp = Blueprint('pricing', __name__)


@bp.route('/<int:cardid>')
def get(cardid):
	# Get the most recent prices
	raw_prices = fetch_query(
		"""
		SELECT DISTINCT ON (cardid, foil)
			low,
			mid,
			high,
			market,
			foil,
			TO_CHAR(created, 'YYYY-MM-DD') AS updated
		FROM price
		WHERE cardid = %(cardid)s
		ORDER BY cardid, foil, created DESC
		""",
		{'cardid': cardid}
	)
	normal = {}
	foil = {}
	for p in raw_prices:
		if p['foil']:
			del p['foil']
			foil = p
		else:
			del p['foil']
			normal = p

	price = {
		'normal': normal,
		'foil': foil
	}

	return jsonify(price)


@bp.route('update', methods=['POST'])
def update():
	# Get any cards that don't have a current price
	cards = fetch_query(
		"""
		SELECT id, tcgplayerid FROM card
		WHERE NOT EXISTS (
			SELECT 1 FROM price WHERE cardid = card.id AND created = current_date
		)
		"""
	)
	batches = [cards[i:i + 250] for i in range(0, len(cards), 250)]
	for b in batches:
		asynchro.fetch_prices.delay(b)

	return jsonify()
