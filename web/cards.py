from flask import Blueprint, jsonify
from web import asynchro, decorators, tcgplayer
from web.utils import strip_unicode
from flasktools.db import fetch_query, mutate_query


bp = Blueprint('cards', __name__)


@bp.route('')
@decorators.auth_required
@decorators.paginated
def get(page, limit):
	pagecount = fetch_query(
		"SELECT CEIL(count(1)::NUMERIC / %(length)s)::INT AS count FROM card",
		{'length': limit},
		single_row=True
	)['count']

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
		LEFT JOIN card_set s ON (s.id = c.card_setid)
		ORDER BY c.id
		LIMIT %(length)s
		OFFSET (%(page)s - 1) * %(length)s
		""",
		{'length': limit, 'page': page}
	)

	return jsonify(page=page, pagecount=pagecount, cards=strip_unicode(cards))


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
