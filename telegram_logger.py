from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
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
admin_id = int(get_env_variable("TelegramUID"))

SUBSCRIBE, SELECT_UNSUBSCRIBE, SELECT_DELETE, OTHER, SELECT_SUBSCRIBE = range(5)

def update_bot(func):
    def func_wrapper(*args, **kwargs):
        global bot
        bot = args[0]
        return func(*args, **kwargs)
    return func_wrapper

def restricted(func):
    def func_wrapper(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != admin_id:
            print(user_id, admin_id)
            print("NOT ADMIN")
            return 
        return func(bot, update, *args, **kwargs)
    return func_wrapper


def all_subscriptions(chat_id):
    subscriptions = []
    for logger in subscribers:
        if chat_id in subscribers[logger]:
            subscriptions.append(logger)
    return subscriptions


subscribers = dict()
def create_logger(logger_id):
    subscribers[logger_id] = set()

def del_logger(logger_id):
    del subscribers[logger_id]

#################
##   HANDLERS   #
#################
@restricted
def all_logs(bot, update):
    title = "<b>ALL LOGS\n</b>"
    update.message.reply_text(title + "\n".join(subscribers.keys()), parse_mode=ParseMode.HTML)

@restricted
def info(bot, update, args):
    ret = "<b>INFO</b>\n "
    for log_id in args:
        ret += '  <b>{}</b>\n'.format(log_id)
        if log_id in args:
            for subs in subscribers[log_id]:
                ret += '    {}\n'.format(subs)
        else:
            ret += "    Doesn't exist\n"
    update.message.reply_text(ret, parse_mode=ParseMode.HTML)

@update_bot
def start(bot, update):
    valid = """I accept /subscribe, /unsubscribe, /show_subscriptions, /create and /delete commands"""
    update.message.reply_text(valid)

### SUBSCRIBE
def subscribe(bot, update):
    update.message.reply_text("Type logger id or /cancel")
    return SELECT_SUBSCRIBE

def subscribe_input(bot, update):
    if update.message.text not in subscribers:
        update.message.reply_text("logger id does not exist. Try again or /cancel")
        return SELECT_SUBSCRIBE
    else:
        subscribers[update.message.text].add(update.message.chat_id)
        update.message.reply_text("You are now subscribed")
    return ConversationHandler.END

def cancel_subscribe(bot, update):
    update.message.reply_text("Didn't subscribe")
    return ConversationHandler.END
## /SUBSCRIBE

### UNSUBSCRIBE
def unsubscribe(bot, update, user_data):
    keyboard = [[InlineKeyboardButton(subscription, callback_data=subscription)] for subscription in all_subscriptions(update.message.chat_id)]
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="Cancel")])
    update.message.reply_text("Select one to unsubscribe", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_UNSUBSCRIBE

def unsubscribe_token_choice(bot, update, user_data):
    query = update.callback_query
    choice = query.data
    if choice == "Cancel":
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Didn't unsubscribe"
        )
        return ConversationHandler.END

    subscribers[choice].remove(query.message.chat_id)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="You were removed from {}'s subscriber list".format(choice)
    )
    return ConversationHandler.END
## /UNSUBSCRIBE

def show_subscriptions(bot, update):
    all_subs = ""
    for logger in subscribers:
        if update.message.chat_id in subscribers[logger]:
            all_subs += logger + "\n"
    if all_subs:
        update.message.reply_text("Currently subscribed to: \n" + all_subs)
    else:
        update.message.reply_text("No active subscriptions")

### CREATE
def create(bot, update, user_data):
    resp = requests.post(basepath + "loggers")
    logger_id = json.loads(resp.text)['logger_id']
    user_data['logger_id'] = logger_id

    keyboard = [[InlineKeyboardButton("Yes", callback_data="Yes"),
                 InlineKeyboardButton("No", callback_data="No")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("logger created at {}. Subscribe?".format(logger_id), reply_markup=reply_markup)

    return SUBSCRIBE

def subscribe_choice(bot, update, user_data):
    query = update.callback_query
    choice = query.data
    logger_id = user_data['logger_id']
    del user_data['logger_id']
    if choice == "Yes":
        subscribers[logger_id].add(query.message.chat_id)
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Subscribed to {}".format(logger_id)
        )
    else:
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Ok, you weren't subscribed to {}".format(logger_id)
        )
    return ConversationHandler.END
### /CREATE

### DELETE
def delete(bot, update, user_data):
    keyboard = [[InlineKeyboardButton(subscription, callback_data=subscription)] for subscription in all_subscriptions(update.message.chat_id)]
    keyboard.append([InlineKeyboardButton("Other", callback_data="Other")])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="Cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Select one to delete", reply_markup=reply_markup)
    return SELECT_DELETE

def delete_token_choice(bot, update, user_data):
    query = update.callback_query
    choice = query.data
    if choice == "Cancel":
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="None deleted"
        )
        return ConversationHandler.END
    if choice == "Other":
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Type logger id or /cancel"
        )
        return OTHER
    resp = requests.delete(basepath + "loggers/{}/".format(choice))
    if json.loads(resp.text)['result']:
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Deleted {}".format(choice)
        )
    return ConversationHandler.END

def other(bot, update):
    if update.message.text not in subscribers:
        update.message.reply_text("logger id does not exist. Try again or /cancel")
        return OTHER
    else:
        resp = requests.delete(basepath + "loggers/{}/".format(update.message.text))
        if json.loads(resp.text)['result']:
            update.message.reply_text("Deleted {}".format(update.message.text))
    return ConversationHandler.END

def cancel_delete(bot, update):
    update.message.reply_text("None deleted")
    return ConversationHandler.END
### /DELETE


def unknown(bot, update):
    """debe ir ULTIMO, responde a los comandos que no activaron alguno de arriba"""
    valid = """I only accept /subscribe, /unsubscribe, /show_subscriptions, /create and /delete commands"""
    update.message.reply_text(valid)


### funcion para notificar
def notify_subscribers(logger_id, message):
    for chat_id in subscribers[logger_id]:
        bot.send_message(chat_id=chat_id, text="{}:\n{}".format(logger_id, message))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=get_env_variable('TELEGRAM_TOKEN'))

    ## RESTRICTED, ONLY ADMIN

    all_handler = CommandHandler('all_logs', all_logs)
    updater.dispatcher.add_handler(all_handler)

    info_handler = CommandHandler('info', info, pass_args=True)
    updater.dispatcher.add_handler(info_handler)

    ## GENERAL USE

    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)

    subscribe_handler = ConversationHandler(
        entry_points=[CommandHandler('subscribe', subscribe)],

        states={
            SELECT_SUBSCRIBE: [MessageHandler((Filters.all & (~ Filters.regex('/cancel'))), subscribe_input)]
            },
        fallbacks=[CommandHandler('cancel', cancel_subscribe)])
    updater.dispatcher.add_handler(subscribe_handler)

    subscriptions_handler = CommandHandler('show_subscriptions', show_subscriptions)
    updater.dispatcher.add_handler(subscriptions_handler)

    create_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create, pass_user_data=True)],

        states={
            SUBSCRIBE: [CallbackQueryHandler(subscribe_choice, pass_user_data=True)]
            },
        fallbacks=[])
    updater.dispatcher.add_handler(create_handler)

    unsubscribe_handler = ConversationHandler(
        entry_points=[CommandHandler('unsubscribe', unsubscribe, pass_user_data=True)],

        states={
            SELECT_UNSUBSCRIBE: [CallbackQueryHandler(unsubscribe_token_choice, pass_user_data=True)]
            },
        fallbacks=[])
    updater.dispatcher.add_handler(unsubscribe_handler)

    delete_handler =ConversationHandler(
        entry_points=[CommandHandler('delete', delete, pass_user_data=True)],

        states={
            SELECT_DELETE: [CallbackQueryHandler(delete_token_choice, pass_user_data=True)],
            OTHER: [MessageHandler((Filters.all & (~ Filters.regex('/cancel'))), other)]
            },
        fallbacks=[CommandHandler('cancel', cancel_delete)])
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

