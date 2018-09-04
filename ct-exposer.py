import sys
import requests
import urllib3
import re
import gevent
from gevent import socket
from gevent.pool import Pool

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

def main(domain):
    domainsFound = {}
    domainsNotFound = {}
    print("[+]: Downloading domain list...")
    response = collectResponse(domain)
    print("[+]: Download of domain list complete.")
    domains = collectDomains(response)
    print("[+]: Parsed %s domain(s) from list." % len(domains))
    
    pool = Pool(15)
    greenlets = [pool.spawn(resolve, domain) for domain in domains]
    pool.join(timeout=1)
    for greenlet in greenlets:
        val=greenlet.value
        if val[1] != 'none':
            domainsFound[val[0]] = val[1]
        else:
            domainsNotFound[val[0]] = val[1]

    print("\n[+]: Domains found:")
    printDomains(domainsFound)
    print("\n[+]: Domains with no DNS record:")
    printDomains(domainsNotFound)

def resolve(domain):
    try:
        return(domain,socket.gethostbyname(domain))
    except:
        return(domain,'none')

def printDomains(domains):
    for domain in sorted(domains):
        print("%s\t%s" % (domains[domain], domain))

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
    #print(response.status_code)
    #print(response.text)
    return response

def collectDomains(response):
    domains = []
    restring = re.compile(r"cn\\u003d(.*?)(\"|,)", re.MULTILINE)
    match = re.findall(restring, response.text)
    if match:
        for domain in match:
            #The following line is meant to avoid adding wildcard domains, as these will not resolve.
            if((domain[0] not in domains) and not (re.search("^\*\.", domain[0]))):
                domains.append(domain[0])
    return domains

if __name__ == '__main__':
    if len(sys.argv) != 2:
    	print("Usage: python ct-exposer.py domain.com")
    	sys.exit(1) 
    main(sys.argv[1])

