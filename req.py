import requests
import json

basepath = "http://telegramrest.freemyip.com:5000/"

# # crear logger, devuelve {"logger_id":"O6WE566ZOPYZ"}
# resp = requests.post(basepath + "loggers")
# print(resp.text)
# logger_id = json.loads(resp.text)['logger_id']


# logear texto
logger_id = "R3WCE0UV9FRZ"
# resp = requests.post(basepath + "loggers/{}/".format(logger_id), json=json.dumps({'text': "Hello world"}))
# print(resp.text)


# eliminar logger
resp = requests.delete(basepath + "loggers/{}".format(logger_id))
print(resp.text)
