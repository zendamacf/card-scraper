from flask import Blueprint, jsonify
from web import asynchro, decorators, tcgplayer
from web.utils import strip_unicode
from flasktools.db import fetch_query, mutate_query


bp = Blueprint('cards', __name__)


@bp.route('')
@decorators.auth_required
@decorators.paginated
def get(lastid, limit):
	cards = fetch_query(
		"""
		SELECT
			c.id,
			c.collectornumber,
			c.name,
			c.rarity,
			c.type,
			c.power,
			c.toughness,
			c.oracletext,
			c.flavortext,
			c.url,
			c.imageurl,
			s.name AS setname,
			s.code AS setcode
		FROM card c
		INNER JOIN card_set s ON (s.id = c.card_setid)
		WHERE CASE WHEN %(lastid)s IS NOT NULL THEN c.id > %(lastid)s ELSE true END
		ORDER BY c.id
		LIMIT %(length)s
		""",
		{'length': limit, 'lastid': lastid}
	)

	lastid = cards[-1]['id'] if len(cards) > 0 else None

	return strip_unicode(cards), lastid


# TODO: Protect this route from DDOS, etc
@bp.route('update', methods=['GET'])
def update():
	print('Getting sets')
	groups = tcgplayer.get_all_groups()
	mutate_query(
		"""
		INSERT INTO card_set (tcgplayerid, name, code, released)
		SELECT %(groupId)s, %(name)s, %(abbreviation)s, %(publishedOn)s
		WHERE NOT EXISTS (SELECT 1 FROM card_set WHERE tcgplayerid = %(groupId)s)
		""",
		groups,
		executemany=True
	)

	print('Getting cards')
	for g in sorted(groups, key=lambda i: i['name']):
		asynchro.fetch_cards.delay(g['groupId'], g['name'])

	return jsonify()
