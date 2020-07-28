from flask import Flask, request, got_request_exception, jsonify
import rollbar
import rollbar.contrib.flask

from flasktools import handle_exception
from flasktools.db import disconnect_database

from web import config

app = Flask(__name__)
app.secret_key = config.SECRETKEY

# Importing below app init so Celery works
from web.cards import bp as cards_bp
from web.pricing import bp as pricing_bp

app.register_blueprint(cards_bp, url_prefix='/cards')
app.register_blueprint(pricing_bp, url_prefix='/pricing')


@app.before_first_request
def init_rollbar():
	if not hasattr(config, 'TESTMODE'):
		env = 'production'
		if request.remote_addr == '127.0.0.1':
			env = 'development'
		rollbar.init(
			config.ROLLBAR_TOKEN,
			environment=env
		)

		# send exceptions from `app` to rollbar, using flask's signal system.
		got_request_exception.connect(rollbar.contrib.flask.report_exception, app)


@app.errorhandler(500)
def internal_error():
	return handle_exception()


@app.teardown_appcontext
def teardown(e):
	disconnect_database()


@app.route('/ping')
def ping():
	return jsonify(ping='pong')


@app.route('/')
def hello():
	return 'hello world'
