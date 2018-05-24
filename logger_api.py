#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response
import string
import random
import json
import time
from telegram_logger import notify_subscribers, create_logger, del_logger

app = Flask(__name__)


class logger:
	def __init__(self, logger_id):
		self.id = logger_id
		self.logs = []


	def new_log(self, text):
		self.logs.append((time, text))

	def __getitem__(self, idx):
		return self.logs[idx]

	def __str__(self):
		return str(self.id)

	def all_logs(self):
		all_logs = ""
		for log in self.logs:
			all_logs += log[1] + "\n"
		return all_logs


loggers = {}

def generate_random_id(N):
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))


@app.route('/loggers/<logger_id>', methods=['GET'])
def get_logger(logger_id):
	if not logger_id in loggers:
		abort(404)
	return jsonify({'logger_id': str(loggers[logger_id])})


@app.route('/loggers', methods=['POST'])
def new_logger():
	logger_id = generate_random_id(12)
	loggers[logger_id] = logger(logger_id)
	create_logger(logger_id)
	return jsonify({'logger_id': str(loggers[logger_id])}), 201


@app.route('/loggers/<logger_id>/', methods=['POST'])
def create_log(logger_id):
	print(request.json)
	if not request.json or not 'text' in request.json:
		abort(400)
	logger = loggers[logger_id]
	params = json.loads(request.json)
	logger.new_log(params['text'])
	notify_subscribers(logger_id, params['text'])
	return jsonify({'result': True}), 201


@app.route('/loggers/<logger_id>', methods=['DELETE'])
def delete_task(logger_id):
	if not logger_id in loggers:
		abort(404)
	notify_subscribers(logger_id, "logger: {} no longer exists".format(logger_id))
	del loggers[logger_id]
	del_logger(logger_id)
	return jsonify({'result': True})


@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
	app.run(debug=True)