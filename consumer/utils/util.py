import re
from iocextract import extract_iocs, extract_hashes, extract_emails, extract_urls, extract_ips
import torch.nn as nn


def clean_tweet(tweet): 
  temp = tweet.lower()
  temp = temp.replace('\n', ' ')
  temp = re.sub("@[A-Za-z0-9_]+","", temp)
  temp = re.sub("#","", temp)
  for ioc in extract_iocs(temp):
      temp = temp.replace(ioc, '')
  temp = re.sub("[^a-z0-9]"," ", temp)
  temp = temp.split()
  temp = " ".join(word for word in temp)
  if len(temp) == 0:
      return
  return temp


def extract_indicator_of_compromise(data):
  list_of_incdicators = ['[.', '(.)', '\.', '{.}', '[@]', '(@)', '{@}', ':\\', 'hxxp', '[/]', 'hxpp']
  iocs = {}

  iocs['text'] = data['text']
  iocs['created_at'] = data['created_at']
  iocs['id'] = data['id_str']

  tweet = data['text']

  # urls
  urls = []
  for ioc in extract_urls(tweet):
    for real_ioc in list_of_incdicators:
      if real_ioc in ioc:
        urls.append([x for x in extract_urls(ioc, refang=True)][0])
  iocs['urls'] = list(set(urls))

  # emails
  emails = []
  for ioc in extract_emails(tweet):
    for real_ioc in list_of_incdicators:
      if real_ioc in ioc:
        emails.append([x for x in extract_emails(ioc, refang=True)])
  iocs['emails'] = list(set(emails))

  # hashes
  hashes = []
  for ioc in extract_hashes(tweet):
    for real_ioc in list_of_incdicators:
      if real_ioc in ioc:
        hashes.append([x for x in extract_hashes(ioc, refang=True)])
  iocs['hashes'] = list(set(hashes))

  ioc_exists=True

  if len(iocs['urls']) == 0 and len(iocs['emails']) == 0 and len(iocs['hashes']) == 0:
    ioc_exists = False

  return ioc_exists, iocs


class BERT_Arch(nn.Module):

    def __init__(self, bert):
      
      super(BERT_Arch, self).__init__()

      self.bert = bert 
      
      # dropout layer
      self.dropout = nn.Dropout(0.1)
      
      # relu activation function
      self.relu =  nn.ReLU()

      # dense layer 1
      self.fc1 = nn.Linear(768,512)
      
      # dense layer 2 (Output layer)
      self.fc2 = nn.Linear(512,2)

      #softmax activation function
      self.softmax = nn.LogSoftmax(dim=1)

    #define the forward pass
    def forward(self, sent_id, mask):

      #pass the inputs to the model  
      _, cls_hs = self.bert(sent_id, attention_mask=mask)
      
      x = self.fc1(cls_hs)

      x = self.relu(x)

      x = self.dropout(x)

      # output layer
      x = self.fc2(x)
      
      # apply softmax activation
      x = self.softmax(x)

      return x