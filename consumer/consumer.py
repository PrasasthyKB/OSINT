import numpy as np
import torch
from transformers import AutoModel, BertTokenizerFast
from kafka import KafkaConsumer
import os
import json
from elasticsearch import Elasticsearch
from uuid import uuid4


from utils.util import clean_tweet, extract_indicator_of_compromise, BERT_Arch

TOPIC_NAME = "TwitterIOC"
KAFKA_SERVER = "128.214.254.195:9093"
ELASTIC_SERVER= "http://128.214.255.133:9200"
index_name = 'twitter_stream_test'

consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers = KAFKA_SERVER, value_deserializer=lambda m: json.loads(m.decode('utf-8')))


es = Elasticsearch([ELASTIC_SERVER])


print(es.indices.exists(index=index_name))


if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)
    print(f'created elasticsearch index {index_name}')



bert = AutoModel.from_pretrained('bert-base-uncased',return_dict=False)
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased',return_dict=False)


device = torch.device("cpu")
path = 'saved_weights.pt'
model = BERT_Arch(bert)
model = model.to(device)
model.load_state_dict(torch.load(path, map_location=device))
print('model loaded')


def classify_tweet(tweet):
    text = [tweet]
    sent_id = tokenizer.batch_encode_plus(text, padding=True)
    test_seq = torch.tensor(sent_id['input_ids'])
    test_mask = torch.tensor(sent_id['attention_mask'])
    with torch.no_grad():
      preds = model(test_seq.to(device), test_mask.to(device))
      preds = preds.detach().cpu().numpy()
    preds = np.argmax(preds, axis = 1)
    return preds[0]


def analyze_data(data):
    if data['text'] is None or data['text'] == '':
        print('data is none')
        return
    cleaned_tweet = clean_tweet(data['text'])
    if cleaned_tweet is None:
      return
    print('TWEET: ', data['text'])
    if classify_tweet(cleaned_tweet) == 1:
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


for data in consumer:
    
    value = data.value
    print('data is received')

    analyze_data(value)