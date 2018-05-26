from telegram.ext import Updater
import requests
import json

TOKEN = "592726549:AAFkiTJP4GAIGYcktxIHibwReBKjZa56Hh0"
updater = Updater(token=TOKEN)

subscribers = dict()
def create_logger(logger_id):
	subscribers[logger_id] = {}

def del_logger(logger_id):
	del subscribers[logger_id]

#### responder a comandos

from telegram.ext import CommandHandler

def subscribe(bot, update, args):
	if not args:
		bot.send_message(chat_id=update.message.chat_id, text="You must supply the logger id: /subscribe logger_id")
	elif args[0] not in subscribers:
		bot.send_message(chat_id=update.message.chat_id, text="logger_id doesn't exist")
	elif update.message.chat_id in subscribers[args[0]]:
		bot.send_message(chat_id=update.message.chat_id, text="You were subscribed already")
	else:
		subscribers[args[0]][update.message.chat_id] = bot
		bot.send_message(chat_id=update.message.chat_id, text="You are now subscribed")
		requests.post("http://127.0.0.1:5000/loggers/{}/".format(args[0]), json=json.dumps({'text': "Welcome {}".format(update.message.username)}))
subscribe_handler = CommandHandler('subscribe', subscribe, pass_args=True)
updater.dispatcher.add_handler(subscribe_handler)

def unsubscribe(bot, update, args):
	if not args:
		bot.send_message(chat_id=update.message.chat_id, text="You must supply the logger id: /unsubscribe logger_id")
	elif args[0] not in subscribers:
		bot.send_message(chat_id=update.message.chat_id, text="logger_id doesn't exist")
	elif update.message.chat_id not in subscribers[args[0]]:
		bot.send_message(chat_id=update.message.chat_id, text="You weren't subscribed")
	else:
		bot.send_message(chat_id=update.message.chat_id, text="You were removed from subscriber list")
		del subscribers[args[0]][update.message.chat_id]
		requests.post("http://127.0.0.1:5000/loggers/{}/".format(args[0]), json=json.dumps({'text': "{} has unsubscribed".format(update.message.username)}))
unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe, pass_args=True)
updater.dispatcher.add_handler(unsubscribe_handler)


def show_subscriptions(bot, update):
	all_subs = ""
	for logger in subscribers.keys():
		if update.message.chat_id in subscribers[logger]:
			all_subs += logger + "\n"
	if all_subs:
		bot.send_message(chat_id=update.message.chat_id, text="Currently subscribed to: \n" + all_subs)
	else:
		bot.send_message(chat_id=update.message.chat_id, text="No active subscriptions")
subscriptions_handler = CommandHandler('show_subscriptions', show_subscriptions)
updater.dispatcher.add_handler(subscriptions_handler)


def create(bot, update):
	resp = requests.post("http://127.0.0.1:5000/loggers")
	logger_id = json.loads(resp.text)['logger_id']
	bot.send_message(chat_id=update.message.chat_id, text="logger created at " + str(logger_id))
create_handler = CommandHandler('create', create)
updater.dispatcher.add_handler(create_handler)


def create_and_subscribe(bot, update):
	resp = requests.post("http://127.0.0.1:5000/loggers")
	logger_id = json.loads(resp.text)['logger_id']
	bot.send_message(chat_id=update.message.chat_id, text="Welcome {}".format(update.message.username))
	subscribers[logger_id][update.message.chat_id] = bot
create_and_subscribe_handler = CommandHandler('create&subscribe', create_and_subscribe)
updater.dispatcher.add_handler(create_and_subscribe_handler)


def delete(bot, update, args):
	if not args:
		bot.send_message(chat_id=update.message.chat_id, text="You must supply the logger id: /subscribe logger_id")
	elif args[0] not in subscribers:
		bot.send_message(chat_id=update.message.chat_id, text="logger_id doesn't exist")
	else:
		requests.delete("http://127.0.0.1:5000/loggers/{}".format(args[0]))
		bot.send_message(chat_id=update.message.chat_id, text="Deleted")
delete_handler = CommandHandler('delete', delete, pass_args=True)
updater.dispatcher.add_handler(delete_handler)


from telegram.ext import MessageHandler, Filters
def unknown(bot, update):
	"""debe ir ULTIMO, responde a los comandos que no activaron alguno de arriba"""
	valid = """I accept /subscribe, /unsubscribe, /show_subscriptions, /create, /create&subscribe and /delete commands"""
	bot.send_message(chat_id=update.message.chat_id, text=valid)
unknown_handler = MessageHandler(Filters.command, unknown)
updater.dispatcher.add_handler(unknown_handler)


### funcion para notificar
def notify_subscribers(logger_id, message):
	for chat_id in subscribers[logger_id].keys():
		subscribers[logger_id][chat_id].send_message(chat_id=chat_id, text="{}:\n{}".format(logger_id, message))


### iniciar el bot 

updater.start_polling()

