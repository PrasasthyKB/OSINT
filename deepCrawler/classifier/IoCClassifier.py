import json
import os
import datetime
from uuid import uuid4

from utils import extract_iocs

from kafka import KafkaConsumer, KafkaProducer
from elasticsearch import Elasticsearch

import Text_classification

CONFIG_PATH = "config.json"

with open(CONFIG_PATH, 'r') as f:
    config = json.loads(f.read())

if __name__ == "__main__":
    consumer = KafkaConsumer(
        config["KAFKA_CONSUME_TOPIC_NAME"],
        bootstrap_servers=config["KAFKA_SERVER"],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest', group_id=config["KAFKA_CONSUMER_GROUP"])
    producer = KafkaProducer(bootstrap_servers=config["KAFKA_SERVER"])

    es = Elasticsearch(
        config["ELASTICSEARCH_SERVER"])

    classifier_instance = Text_classification.load()

    for data in consumer:
        text = data.value["text"]
        pred = classifier_instance.classify_text(text)
        if pred:
            print("Found relevant web page. Attempting to extract IoCs...")
            iocs = extract_iocs(text, data.value["url"])
            # Skip if no iocs found
            if not iocs:
                print("No IoCs found. Skipping...")
                continue

            print("Found some IoCs. Proceeding to update Kafka and ElasticSearch...")
            # Create payload for kafka and elasticsearch and enrich it with metadata
            payload = {
                key: data.value[key]
                for key in
                ["url", "spider_name", "date_inserted"]}
            # Rename timestamp field for elasticsearch
            payload['@timestamp'] = datetime.datetime.fromisoformat(
                payload["date_inserted"]).isoformat()
            del payload["date_inserted"]

            payload["iocs"] = iocs
            json_payload = json.dumps(payload)
            json_payload = str.encode(json_payload)
            producer.send(config["KAFKA_PRODUCE_TOPIC_NAME"], json_payload)
            producer.flush()

            try:
                res = es.index(
                    index=config["ELASTICSEARCH_INDEX_NAME"],
                    id=str(uuid4()),
                    document=json_payload)
            except Exception as e:
                print('Error : ', e)
