import requests
import json

# resp = requests.post("http://127.0.0.1:5000/loggers")
# print(resp.text)
# token = json.loads(resp.text)['logger_id']

token = "YUBZXPYNZ1Y6"
resp = requests.post("http://127.0.0.1:5000/loggers/{}/".format(token), json=json.dumps({'text': "hello world"}))
print(resp.text)