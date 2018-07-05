# Telegram logger

Provides a REST api for sending log messages through telegram. It follows a subscriber model where users subscribe to a specific logger using a token, and will receive all subsecuent logs in their telegram acounts via a bot.

The bot can be found [here](https://t.me/LossNotifierBot).

## Creating and subscribing

Loggers can be created by using the bot (with `/create`) or by using the REST API. Inmediately after creating the bot lets us subscribe to the logger to begin receiving updates, or we can subscribe manually by using `/subscribe` and entering the logger id. Loggers can also be created by POSTing to [http://telegramrest.freemyip.com:5000/loggers](http://telegramrest.freemyip.com:5000/loggers). The response will be a json object where the logger id (needed to `/subscribe` via the bot) can be found under the key `logger_id`.

~~~python
import requests
import json

basepath = "http://telegramrest.freemyip.com:5000/"

# create logger with api, returns token as json {"logger_id":"TOKEN"}
resp = requests.post(basepath + "loggers")
logger_id = json.loads(resp.text)['logger_id']
~~~

To list all current subscriptions we can use `/show_subscritptions` in the bot. To unsubscribe from a logger `/unsubscribe` can be used. If the logger wont be used anymore using `/delete` unsubscribes all subscribers from the selected logger and deletes it from memory (so no one can subscribe to it later). Alternatively, we can use the API to DELETE. 
~~~python
resp = requests.delete(basepath + "loggers/{}/".format(logger_id))
~~~

## Logging

Regardless of how the logger were created (API or bot) logs are always posted through the APi. Notifications are sent through telegram to all the subscribers of the specific log. 

The examples below sends numbers from 0 to 9 in two second intervals. The bot is created using the API, so users wanting to receive notificationss should call `/subscribe` within the bot. Then, when prompted, they can enter the logger_id to start receiving notifications.

~~~python
import requests
import json
import time

basepath = "http://telegramrest.freemyip.com:5000/"

# create logger, returns token as json {"logger_id":"O6WE566ZOPYZ"}
resp = requests.post(basepath + "loggers")
logger_id = json.loads(resp.text)['logger_id']
print("use {} to /subscribe in the bot".format(logger_id))

# log text
for i in range(10):
    resp = requests.post(basepath + "loggers/{}/".format(logger_id), json=json.dumps({'text': str(i)}))
    time.sleep(2)

# delete logger
resp = requests.delete(basepath + "loggers/{}/".format(logger_id))
~~~

### Logging images

Images can also be sent using the API by using the following command (replacing test.jpeg with the correct image path):

~~~python
url = basepath + "loggers/{}/".format(logger_id)
files = {'media': open('test.jpeg', 'rb')}
resp = requests.post(url, files=files)
~~~

## Full Log

To obtain the full log (json encoded with timestamps, but no images) use:

~~~python
url = basepath + "loggers/{}/full_log".format(logger_id)
resp = requests.get(url)
print(resp.text)
~~~

## Subscribe URL

A url to automatically subscribe to a certain logger can be found with GET.

~~~python
url = basepath + "loggers/{}".format(logger_id)
resp = requests.get(url)
print(resp.text)   >>   {"logger_id": "QE7NDJZ87H7Y",  "path": "https://t.me/LossNotifierBot?start=LOGGERID"}
~~~

