from collections import OrderedDict
from flasktools import strip_unicode_characters


def strip_unicode(rows: list) -> list:
	"""Strip unicode characters out of a list of `OrderedDict`.
	Returns a new copy without mutating the original list."""
	cleaned = []
	for row in rows:
		new_row = OrderedDict()
		for key, value in row.items():
			if isinstance(value, str):
				value = strip_unicode_characters(value)
			new_row[key] = value
		cleaned.append(new_row)

	return cleaned
