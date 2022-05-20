from flask import Flask
import json
from kafka import KafkaProducer, KafkaConsumer
import tweepy
import logging
import numpy as np
from elasticsearch import Elasticsearch
from uuid import uuid4


from utils.util import json_reader, extract_indicator_of_compromise

import Tweet_classification

app = Flask(__name__)

TOPIC_NAME = "TwitterIOC"
KAFKA_SERVER = "128.214.254.195:9093"
ELASTIC_SERVER= "http://128.214.255.133:9200"
index_name = 'twitter_stream_test'

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



producer = KafkaProducer(bootstrap_servers = KAFKA_SERVER, api_version = (0, 11, 15))

auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)

api = tweepy.API(auth)

consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers = KAFKA_SERVER, value_deserializer=lambda m: json.loads(m.decode('utf-8')))


es = Elasticsearch([ELASTIC_SERVER])


if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)
    print(f'created elasticsearch index {index_name}')

classifier_instance = Tweet_classification.load()


def classify_tweet(tweet):
    prediction = classifier_instance.classify_tweet(tweet)
    return prediction


def analyze_data(data):
    if data['text'] is None or data['text'] == '':
        print('data is none')
        return

    print('TWEET: ', data['text'])
    if classify_tweet(data['text']) == 1:
        print(f'RELEVANT - {data["text"]} \n list of IOCs: ')
        ioc_exits, iocs = extract_indicator_of_compromise(data)
        if not ioc_exits:
          print('no ioc detected')
          return
        print(iocs)
        id = str(uuid4())
        try: 
          res = es.index(index=index_name, id=id, document=iocs)
        except Exception as e:
          print('Error : ', e)
    else:
        print('NOT RELEVANT')





@app.route('/kafka/pushToConsumers', methods=['POST'])
def send_to_broker(json_data):
    
    json_payload = json.dumps(json_data)
    json_payload = str.encode(json_payload)
    
    # push data into INFERENCE TOPIC
    producer.send(TOPIC_NAME, json_payload)
    producer.flush()
    print(json_data['text'])
    print('Sent to consumer')
    return


class IOCStreamListener(tweepy.Stream):

    def on_status(self, status):
        send_to_broker(status._json)


if __name__ == "__main__":

    tweet_listener = IOCStreamListener(consumer_key, consumer_secret, access_token, access_token_secret)

    # tweet_listener.filter(track=["ioc","indicator_of_compromise", "maldoc", "spam", "malspam", "threathunting", "blacklist",
    #                              "datasecurity","linux","ransomware","phishing","ethicalhacking","cybersecuritytraining",
    #                              "cybersecurityawareness","malware","informationsecurity","infosec", "threatintel"
    #                              "cybercrip","hacker","cybercrime","cybersecurityengineer","android", "opendir", "osint",
    #                              "ios","networking","cyberattack","kalilinux","anonymous", "cybersecurityengineer"], threaded=True, languages=['en'])

    tweet_listener.filter(track=["ioc"], threaded=True, languages=['en'])

    for data in consumer:
    
        value = data.value
        print('data is received')

        analyze_data(value)

