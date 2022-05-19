import os
from flask import Flask
import json
from kafka import KafkaProducer
import tweepy
import logging


from utils.util import json_reader

config_file = 'config.json'

conf = json_reader(config_file)


# check if the config is json
if not isinstance(conf, dict):
    raise Exception(f'Config file: {config_file} is not json')

# check if neccessary keys exist in conf
keys = ['consumer_key', 'consumer_secret', 'access_token', 'access_token_secret']
for key in keys:
    if key not in conf:
        raise Exception(f'key: {key} is not found')

# Twitter API credentials
consumer_key = conf['consumer_key']
consumer_secret = conf['consumer_secret']
access_token = conf['access_token']
access_token_secret = conf['access_token_secret']


app = Flask(__name__)
TOPIC_NAME = "TwitterIOC"
KAFKA_SERVER = "128.214.254.195:9093"

producer = KafkaProducer(bootstrap_servers = KAFKA_SERVER, api_version = (0, 11, 15))

auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)

api = tweepy.API(auth)

@app.route('/kafka/pushToConsumers', methods=['POST'])
def kafkaProducer(json_data):
    
    json_payload = json.dumps(json_data)
    json_payload = str.encode(json_payload)
    
    # push data into INFERENCE TOPIC
    producer.send(TOPIC_NAME, json_payload)
    producer.flush()
    print(json_data['text'])
    print('Sent to consumer')
    return


class CustomStreamListener(tweepy.Stream):

    def on_status(self, status):
        kafkaProducer(status._json)


if __name__ == "__main__":
    tweet_listener = CustomStreamListener(consumer_key, consumer_secret, access_token, access_token_secret)
    # tweet_listener.filter(track=["ioc","indicator_of_compromise", "maldoc", "spam", "malspam", "threathunting", "blacklist",
    #                              "datasecurity","linux","ransomware","phishing","ethicalhacking","cybersecuritytraining",
    #                              "cybersecurityawareness","malware","informationsecurity","infosec", "threatintel"
    #                              "cybercrip","hacker","cybercrime","cybersecurityengineer","android", "opendir", "osint",
    #                              "ios","networking","cyberattack","kalilinux","anonymous", "cybersecurityengineer"], threaded=True, languages=['en'])
    tweet_listener.filter(track=["ioc"], threaded=True, languages=['en'])
    
    app.run(debug=False, port = 5000)