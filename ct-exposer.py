#!/usr/bin/env python3

import requests
import argparse
from gevent import socket
from gevent.pool import Pool

requests.packages.urllib3.disable_warnings()


def main(domain, masscanOutput, urlOutput):
    domainsFound = {}
    domainsNotFound = {}
    if (not masscanOutput and not urlOutput):
        print("[+]: Downloading domain list from crt.sh...")
    response = collectResponse(domain)
    if (not masscanOutput and not urlOutput):
        print("[+]: Download of domain list complete.")
    domains = collectDomains(response)
    if (not masscanOutput and not urlOutput):
        print("[+]: Parsed %s domain(s) from list." % len(domains))
    if len(domains) == 0:
        exit(1)

    pool = Pool(15)
    greenlets = [pool.spawn(resolve, domain) for domain in domains]
    pool.join(timeout=1)
    for greenlet in greenlets:
        result = greenlet.value
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; \
               Win64; x64) AppleWebKit/537.36 (KHTML, like \
               Gecko) Chrome/63.0.3239 Safari/537.36'}
    url = 'https://crt.sh/?q=' + domain + '&output=json'
    try:
        response = requests.get(url, headers=headers, verify=False)
    except:
        print("[!]: Connection to server failed.")
        exit(1)
    try:
        domains = response.json()
        return domains
    except:
        print("[!]: The server did not respond with valid json.")
        exit(1)


def collectDomains(response):
    domains = set()
    for domain in response:
        domains.add(domain['common_name'])
        if '\n' in domain['name_value']:
            domlist = domain['name_value'].split()
            for dom in domlist:
                domains.add(dom)
        else:
            domains.add(domain['name_value'])
    return domains


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", type=str, required=True,
                        help="domain to query for CT logs, e.g.: domain.com")
    parser.add_argument("-u", "--urls", default=0, action="store_true",
                        help="ouput results with https:// urls for \
                        domains that resolve, one per line.")
    parser.add_argument("-m", "--masscan", default=0, action="store_true",
                        help="output resolved IP address, one per line. \
                        Useful for masscan IP list import \"-iL\" format.")
    args = parser.parse_args()
    main(args.domain, args.masscan, args.urls)
