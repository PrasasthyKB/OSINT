import json
import ipaddress
import itertools
from urllib.parse import urlparse

import requests

import html2text

from kafka import KafkaConsumer, KafkaProducer
import iocextract

CONSUME_TOPIC_NAME = "IoCRelevants"
PRODUCE_TOPIC_NAME = "DwebIoCs"
CONSUMER_GROUP = "DwebClassifier"
KAFKA_SERVER = "128.214.254.195:9093"

consumer = KafkaConsumer(CONSUME_TOPIC_NAME, bootstrap_servers=KAFKA_SERVER, value_deserializer=lambda m: json.loads(
    m.decode('utf-8')), auto_offset_reset='earliest')
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

r = requests.get(
    "https://securelist.com/moonbounce-the-dark-side-of-uefi-firmware/105468/")

text = html2text.html2text(r.text)

iocs = []

# Extract hashes
for hash_ in iocextract.extract_hashes(text):

    hash_type = 'misc.'
    if len(hash_) == 32:
        hash_type = "MD5"
    elif len(hash_) == 40:
        hash_type = "SHA1"
    elif len(hash_) == 64:
        hash_type = "SHA256"
    elif len(hash_) == 128:
        hash_type = "SHA512"

    iocs.append({'hash': {"hash_type": hash_type, "ioc": hash_}})

# Extract YARA rules
for yara in iocextract.extract_yara_rules(text):
    iocs.append({'yara': {"ioc": yara}})

# Extract emails
for email in iocextract.extract_emails(text, refang=True):
    iocs.append({'email': {"ioc": email}})

# Extract IPs
for ip_addr in iocextract.extract_ips(text):

    # Skip if ip is not defanged
    if ip_addr == iocextract.refang_ipv4(ip_addr):
        continue
    ip_addr = iocextract.refang_ipv4(ip_addr)
    ip_addr.replace('[', '').replace(']', '').split(
        '/')[0].split(':')[0].split(' ')[0]
    try:
        ip_addr = ipaddress.IPv4Address(ip_addr)
        ip_ver = "IPv4"
    except ValueError:
        try:
            ip_addr = ipaddress.IPv6Address(ip_addr)
            ip_ver = "IPv6"
        except ValueError:
            print(f"ip {ip_addr} format not recognized!")
            continue
    iocs.append({'ip': {"ver": ip_ver, "ioc": str(ip_addr)}})

# Extract URLs
urls = itertools.chain(
    iocextract.extract_unencoded_urls(text),
    iocextract.extract_encoded_urls(text, refang=True),
)
for url in urls:
    # Skip if url is not defanged
    if url == iocextract.refang_url(url):
        continue
    url = iocextract.refang_url(url)
    possible_ip = urlparse(url).netloc.split(':')[0].replace(
        '[', '').replace(']', '').replace(',', '.')

    # Skip if url is ip
    try:
        ipaddress.IPv4Address(possible_ip)
        continue
    except ValueError:
        try:
            ipaddress.IPv6Address(possible_ip)
            continue
        except ValueError:
            pass

    try:
        url_domain = urlparse(url).netloc.split(':')[0]
    # Trouble parsing url, just skip
    except ValueError:
        continue
    # Skip if url is in the same domain as current page
    if url_domain == urlparse(r.url).netloc:
        print(f"Found url with same domain: {url}")
        continue
    iocs.append({'url': {"domain": url_domain, "ioc": url}})

# Remove duplicates
unique_iocs_set = set()
unique_iocs_list = []
for record in iocs:
    if list(record.values())[0]['ioc'] not in unique_iocs_set:
        unique_iocs_set.add(list(record.values())[0]['ioc'])
        unique_iocs_list.append(record)

print(unique_iocs_list)
