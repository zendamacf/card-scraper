from flask import Blueprint, jsonify
from flasktools.db import fetch_query
from web import asynchro


bp = Blueprint('pricing', __name__)


@bp.route('')
def get():
	pass


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
