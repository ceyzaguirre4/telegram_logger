from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import requests
import json
import os


def get_env_variable(var_name):
    """ Get the environment variable or return exception """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise Exception(error_msg)


basepath = "http://0.0.0.0:5000/"
bot = None


def update_bot(func):
    def func_wrapper(*args, **kwargs):
        global bot
        bot = args[0]
        return func(*args, **kwargs)
    return func_wrapper


subscribers = dict()
def create_logger(logger_id):
    subscribers[logger_id] = set()

def del_logger(logger_id):
    del subscribers[logger_id]


#### responder a comandos

@update_bot
def start(bot, update):
    valid = """I accept /subscribe, /unsubscribe, /show_subscriptions, /create, /create_subscribe and /delete commands"""
    update.message.reply_text(valid)


def subscribe(bot, update, args):
    if not args:
        update.message.reply_text("You must supply the logger id: /subscribe logger_id")
    elif args[0] not in subscribers:
        update.message.reply_text("logger_id doesn't exist")
    elif update.message.chat_id in subscribers[args[0]]:
        update.message.reply_text("You were subscribed already")
    else:
        subscribers[args[0]].add(update.message.chat_id)
        update.message.reply_text("You are now subscribed")
        requests.post(basepath + "loggers/{}/".format(args[0]), json=json.dumps({'text': "Welcome {}".format(update.message.username)}))


def unsubscribe(bot, update, args):
    if not args:
        update.message.reply_text("You must supply the logger id: /unsubscribe logger_id")
    elif args[0] not in subscribers:
        update.message.reply_text("logger_id doesn't exist")
    elif update.message.chat_id not in subscribers[args[0]]:
        update.message.reply_text("You weren't subscribed")
    else:
        subscribers[args[0]].remove(update.message.chat_id)
        update.message.reply_text("You were removed from subscriber list")
        requests.post(basepath + "loggers/{}/".format(args[0]), json=json.dumps({'text': "{} has unsubscribed".format(update.message.username)}))


def show_subscriptions(bot, update):
    all_subs = ""
    for logger in subscribers:
        if update.message.chat_id in subscribers[logger]:
            all_subs += logger + "\n"
    if all_subs:
        update.message.reply_text("Currently subscribed to: \n" + all_subs)
    else:
        update.message.reply_text("No active subscriptions")


def create(bot, update):
    resp = requests.post(basepath + "loggers")
    logger_id = json.loads(resp.text)['logger_id']
    update.message.reply_text("logger created at " + str(logger_id))


def create_and_subscribe(bot, update):
    resp = requests.post(basepath + "loggers")
    logger_id = json.loads(resp.text)['logger_id']
    subscribers[logger_id].add(update.message.chat_id)
    update.message.reply_text("Welcome {}".format(update.message.username))


def delete(bot, update, args):
    if not args:
        update.message.reply_text("You must supply the logger id: /delete logger_id")
    elif args[0] not in subscribers:
        update.message.reply_text("logger_id doesn't exist")
    else:
        resp = requests.delete(basepath + "loggers/{}/".format(args[0]))
        if json.loads(resp.text)['result']:
            update.message.reply_text("Deleted")


def unknown(bot, update):
    """debe ir ULTIMO, responde a los comandos que no activaron alguno de arriba"""
    valid = """I only accept /subscribe, /unsubscribe, /show_subscriptions, /create, /create_subscribe and /delete commands"""
    update.message.reply_text(valid)


### funcion para notificar
def notify_subscribers(logger_id, message):
    for chat_id in subscribers[logger_id]:
        bot.send_message(chat_id=chat_id, text="{}:\n{}".format(logger_id, message))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=get_env_variable('TELEGRAM_TOKEN'))

    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)

    subscribe_handler = CommandHandler('subscribe', subscribe, pass_args=True)
    updater.dispatcher.add_handler(subscribe_handler)

    unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe, pass_args=True)
    updater.dispatcher.add_handler(unsubscribe_handler)

    subscriptions_handler = CommandHandler('show_subscriptions', show_subscriptions)
    updater.dispatcher.add_handler(subscriptions_handler)

    create_handler = CommandHandler('create', create)
    updater.dispatcher.add_handler(create_handler)

    create_and_subscribe_handler = CommandHandler('create_subscribe', create_and_subscribe)
    updater.dispatcher.add_handler(create_and_subscribe_handler)

    delete_handler = CommandHandler('delete', delete, pass_args=True)
    updater.dispatcher.add_handler(delete_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    updater.dispatcher.add_handler(unknown_handler)

    # Start the Bot
    updater.start_polling()

    return updater


if __name__ == '__main__':
    updater = main()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

