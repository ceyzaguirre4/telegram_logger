from telegram.ext import Updater

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
		for chat_id in subscribers[args[0]].keys():
			subscribers[args[0]][chat_id].send_message(chat_id=chat_id, text="{} has subscribed".format(update.message.username))
		subscribers[args[0]][update.message.chat_id] = bot
		bot.send_message(chat_id=update.message.chat_id, text="You are now subscribed")
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
		for chat_id in subscribers[args[0]].keys():
			subscribers[args[0]][chat_id].send_message(chat_id=chat_id, text="{} has unsubscribed".format(update.message.username))
unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe, pass_args=True)
updater.dispatcher.add_handler(unsubscribe_handler)


def show_subscriptions(bot, update):
	all_subs = "Currently subscribed to: \n"
	for logger in subscribers.keys():
		if update.message.chat_id in subscribers[logger]:
			all_subs += logger + "\n"
	bot.send_message(chat_id=update.message.chat_id, text=all_subs)
subscriptions_handler = CommandHandler('show_subscriptions', show_subscriptions)
updater.dispatcher.add_handler(subscriptions_handler)


from telegram.ext import MessageHandler, Filters
def unknown(bot, update):
	"""debe ir ULTIMO, responde a los comandos que no activaron alguno de arriba"""
	valid = """Sorry I can only accept /subscribe, /unsubscribe and /show_subscriptions"""
	bot.send_message(chat_id=update.message.chat_id, text=valid)
unknown_handler = MessageHandler(Filters.command, unknown)
updater.dispatcher.add_handler(unknown_handler)


### funcion para notificar
def notify_subscribers(logger_id, message):
	for chat_id in subscribers[logger_id].keys():
		subscribers[logger_id][chat_id].send_message(chat_id=chat_id, text="{}:\n{}".format(logger_id, message))


### iniciar el bot 

updater.start_polling()


