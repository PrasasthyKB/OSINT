import ipaddress
import itertools
from urllib.parse import urlparse

import iocextract


def get_unique_iocs(iocs):
    unique_iocs_set = set()
    unique_iocs_list = []
    for record in iocs:
        if record['value'] not in unique_iocs_set:
            unique_iocs_set.add(record['value'])
            unique_iocs_list.append(record)
    return unique_iocs_list


def extract_iocs(text, crawled_url):
    iocs = {}

    # Extract hashes
    hashes = []
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

        hashes.append({"type": hash_type, "value": hash_})
    iocs["hash"] = get_unique_iocs(hashes)

    # Extract YARA rules
    yaras = []
    for yara in iocextract.extract_yara_rules(text):
        yaras.append({"value": yara})
    iocs["yara"] = get_unique_iocs(yaras)

    # Extract emails
    emails = []
    for email in iocextract.extract_emails(text, refang=True):
        emails.append({"value": email})
    iocs["email"] = get_unique_iocs(emails)

    # Extract IPs
    ips = []
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
        ips.append({"ip_version": ip_ver, "value": str(ip_addr)})
    iocs["ip_addresses"] = get_unique_iocs(ips)

    # Extract URLs
    url_iocs = []
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
        if url_domain == urlparse(crawled_url).netloc:
            print(f"Found url with same domain: {url}")
            continue
        url_iocs.append({"url_domain": url_domain, "value": url})
    iocs["url"] = get_unique_iocs(url_iocs)

    ioc_found = False
    for key, value in iocs.items():
        if len(value) != 0:
            ioc_found = True
            break
    # Return None if no IoCs found
    if not ioc_found:
        return None
    # Remove duplicates

    return iocs
