import json
from iocextract import extract_iocs, extract_hashes, extract_emails, extract_urls


def json_reader(file_name: str):
    with open(file_name, 'r') as f:
        try:
            return json.loads(f.read())
        except Exception as e:
            return e
        

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
