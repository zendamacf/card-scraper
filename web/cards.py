from flask import Blueprint, jsonify
from web import asynchro, tcgplayer
from flasktools.db import mutate_query


bp = Blueprint('cards', __name__)


@bp.route('')
def get():
	pass


@bp.route('update', methods=['POST'])
def update():
	print('Getting sets')
	groups = tcgplayer.get_all_groups()
	insert_sets(groups)

	print('Getting cards')
	for g in groups:
		asynchro.fetch_cards.delay(g['groupId'], g['name'])

	return jsonify()


def insert_sets(groups):
	mutate_query(
		"""
		INSERT INTO card_set (tcgplayerid, name, released)
		SELECT %(groupId)s, %(name)s, %(publishedOn)s
		WHERE NOT EXISTS (SELECT 1 FROM card_set WHERE tcgplayerid = %(groupId)s)
		""",
		groups,
		executemany=True
	)
