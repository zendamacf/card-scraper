CREATE TABLE card_set (
	id SERIAL PRIMARY KEY,
	tcgplayerid INTEGER NOT NULL,
	name TEXT NOT NULL,
	released DATE NOT NULL
);

CREATE TABLE card (
	id SERIAL PRIMARY KEY,
	tcgplayerid INTEGER NOT NULL,
	card_setid INTEGER NOT NULL REFERENCES card_set(id),
	collectornumber TEXT NOT NULL,
	name TEXT NOT NULL,
	rarity CHAR(1) NOT NULL,
	type TEXT,
	power TEXT,
	toughness TEXT,
	oracletext TEXT,
	flavortext TEXT,
	url TEXT,
	imageurl TEXT
);

CREATE UNIQUE INDEX card_tcgplayerid_idx ON card (tcgplayerid); 

CREATE TABLE price (
	cardid INTEGER NOT NULL REFERENCES card(id),
	low MONEY,
	mid MONEY,
	high MONEY,
	market MONEY,
	foil BOOLEAN NOT NULL DEFAULT FALSE,
	created DATE NOT NULL DEFAULT current_date
);

CREATE UNIQUE INDEX price_created_idx ON price(cardid, foil, created);