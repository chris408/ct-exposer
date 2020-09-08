#!/usr/bin/env python3

import sys
import requests
import re
import argparse
import gevent
from gevent import socket
from gevent.pool import Pool

requests.packages.urllib3.disable_warnings()
                
def main(domain, masscanOutput, urlOutput):
    domainsFound = {}
    domainsNotFound = {}
    if (not masscanOutput and not urlOutput):
        print("[+]: Downloading domain list...")
    response = collectResponse(domain)
    if (not masscanOutput and not urlOutput):
        print("[+]: Download of domain list complete.")
    domains = collectDomains(response)
    if (not masscanOutput and not urlOutput):
        print("[+]: Parsed %s domain(s) from list." % len(domains))
    
    pool = Pool(15)
    greenlets = [pool.spawn(resolve, domain) for domain in domains]
    pool.join(timeout = 1)
    for greenlet in greenlets:
        result=greenlet.value
        if (result):
            for ip in result.values():
                if ip != 'none':
                    domainsFound.update(result)
                else:
                    domainsNotFound.update(result)

    if (urlOutput):
        printUrls(sorted(domains))
    if (masscanOutput):
        printMasscan(domainsFound)
    if (not masscanOutput and not urlOutput):
        print("\n[+]: Domains found:")
        printDomains(domainsFound)
        print("\n[+]: Domains with no DNS record:")
        printDomains(domainsNotFound)

def resolve(domain):
    try:
        return({domain: socket.gethostbyname(domain)})
    except:
        return({domain: "none"})

def printDomains(domains):
    for domain in sorted(domains):
        print("%s\t%s" % (domains[domain], domain))

def printMasscan(domains):
    iplist = set()
    for domain in domains:
        iplist.add(domains[domain])
    for ip in sorted(iplist):
        print("%s" % (ip))

def printUrls(domains):
    for domain in domains:
        print("https://%s" % domain)

def collectResponse(domain):
    headers = {'Host': 'ctsearch.entrust.com',
	       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
	       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	       'Accept-Language': 'en-US,en;q=0.5',
	       'Accept-Encoding': 'gzip, deflate',
               'Referer': 'https://www.entrust.com/ct-search/',
	       'Connection': 'close',
	       'Upgrade-Insecure-Requests': '1',
	       'Content-Length': '0'}

    url = 'https://ctsearch.entrust.com/api/v1/certificates?fields=subjectDN&domain=' + domain + '&includeExpired=true&exactMatch=false&limit=5000'
    response = requests.get(url, headers=headers, verify=False)
    return response

def collectDomains(response):
    domains = []
    restring = re.compile(r"cn\\u003d(.*?)(\"|,)", re.MULTILINE)
    match = re.findall(restring, response.text)
    if match:
        for domain in match:
            #The following line avoids adding wildcard domains, as they will not resolve.
            if((domain[0] not in domains) and not (re.search("^\*\.", domain[0]))):
                domains.append(domain[0])
    return domains

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", type=str, required=True, help="domain to query for CT logs, ex: domain.com")
    parser.add_argument("-u", "--urls", default=0, action="store_true", help="ouput results with https:// urls for domains that resolve, one per line.")
    parser.add_argument("-m", "--masscan", default=0, action="store_true", help="output resolved IP address, one per line. Useful for masscan IP list import \"-iL\" format.")
    args = parser.parse_args()
    main(args.domain, args.masscan, args.urls)

