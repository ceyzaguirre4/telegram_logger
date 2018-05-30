#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, render_template
import string
import random
import json
import datetime
from telegram_logger import create_logger, del_logger, main, text_notify_subscribers, img_notify_subscribers
import signal


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
    ))

app = CustomFlask(__name__)
loggers = {}


class logger:
    def __init__(self, logger_id):
        self.id = logger_id
        self.logs = []

    def new_log(self, text):
        date = datetime.datetime.now()
        self.logs.append((date, text))

    def __getitem__(self, idx):
        return self.logs[idx]

    def __str__(self):
        return str(self.id)

    def all_logs(self):
        all_logs = []
        for log in self.logs:
            all_logs.append([log[0].strftime("%y-%m-%d-%H-%M"), log[1]])
        return all_logs


def generate_random_id(N):
    logger_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
    while logger_id in loggers:
        logger_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
    return logger_id


@app.route('/', methods=['GET'])
def hello():
    return render_template('index.html')


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
    if not request.files and not request.json:
        abort(400)
    elif not logger_id in loggers:
        abort(404)
    elif 'media' in request.files:
        logger = loggers[logger_id]
        file = request.files['media']
        logger.new_log("IMAGE")
        img_notify_subscribers(logger_id, file)
    elif 'text' in request.json:
        logger = loggers[logger_id]
        params = json.loads(request.json)
        logger.new_log(params['text'])
        text_notify_subscribers(logger_id, params['text'])
    else:
        abort(400)
    return jsonify({'result': True}), 201


@app.route('/loggers/<logger_id>/', methods=['DELETE'])
def delete_task(logger_id):
    if not logger_id in loggers:
        abort(404)
    text_notify_subscribers(logger_id, "logger no longer exists".format(logger_id))
    del loggers[logger_id]
    del_logger(logger_id)
    return jsonify({'result': True})


@app.route('/loggers/<logger_id>/full_log', methods=['GET'])
def full_log(logger_id):
    if not logger_id in loggers:
        abort(404)
    logger = loggers[logger_id]
    return jsonify({'full_log': logger.all_logs()})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    updater = main()

    def handler(signum, frame):
        for logger_id in list(loggers.keys()):
            text_notify_subscribers(logger_id, "Logger was removed for server maintenance".format(logger_id))
            del loggers[logger_id]
            del_logger(logger_id)
        updater.stop()
        exit(0)
        
    signal.signal(signal.SIGINT, handler)

    app.run(host='0.0.0.0')
