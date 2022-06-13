import json
import os

import torch
from torch import nn

from transformers import BertTokenizer, BertModel, BertConfig

from kafka import KafkaConsumer, KafkaProducer
import boto3

AWS_CREDS_PATH = "/run/secrets/aws_creds.json"
CONFIG_PATH = "config.json"

with open(AWS_CREDS_PATH, 'r') as f:
    aws_config = json.loads(f.read())

with open(CONFIG_PATH, 'r') as f:
    config = json.loads(f.read())

MODEL_PATH = os.path.join("model_checkpoints/", config["MODEL_FILE_PATH"])

tokenizer = BertTokenizer.from_pretrained(config["TOKENIZER_NAME"])


class BertClassifier(nn.Module):

    def __init__(self, dropout=0.5):

        super(BertClassifier, self).__init__()

        self.bert = BertModel.from_pretrained(config["BASE_MODEL_NAME"])
        self.dropout = nn.Dropout(dropout)
        self.linear = nn.Linear(768, 2)
        self.relu = nn.ReLU()

    def forward(self, input_id, mask):

        _, pooled_output = self.bert(
            input_ids=input_id, attention_mask=mask, return_dict=False)
        dropout_output = self.dropout(pooled_output)
        linear_output = self.linear(dropout_output)
        final_layer = self.relu(linear_output)

        return final_layer


if __name__ == "__main__":
    consumer = KafkaConsumer(
        config["KAFKA_CONSUME_TOPIC_NAME"],
        bootstrap_servers=config["KAFKA_SERVER"],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest', group_id=config["KAFKA_CONSUMER_GROUP"])
    producer = KafkaProducer(bootstrap_servers=config["KAFKA_SERVER"])

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    s3 = boto3.client(
        's3',
        region_name=config["S3_REGION"],
        aws_access_key_id=aws_config["ACCESS_KEY_ID"],
        aws_secret_access_key=aws_config["ACCESS_TOKEN"]
    )
    with open(MODEL_PATH, 'wb') as f:
        s3.download_fileobj(
            config["S3_BUCKET_NAME"],
            config["S3_MODEL_PATH"],
            f)

    if use_cuda:
        model = model.cuda()

    model = BertClassifier()
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    with torch.no_grad():
        for data in consumer:
            print("Received data...")
            text = data.value["text"]
            tokenized = tokenizer(
                text, padding='max_length', max_length=512, truncation=True,
                return_tensors="pt")
            mask = tokenized['attention_mask'].to(device)
            input_id = tokenized['input_ids'].squeeze(1).to(device)

            output = model(input_id, mask)
            pred = output.argmax(dim=1).int()
            if pred:
                json_payload = json.dumps(data.value)
                json_payload = str.encode(json_payload)
                producer.send(config["KAFKA_PRODUCE_TOPIC_NAME"], json_payload)
                producer.flush()
