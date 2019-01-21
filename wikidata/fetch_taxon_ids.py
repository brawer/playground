import re, requests

#payload = {'query': 'SELECT ?item  WHERE { ?item wdt:P31 wd:Q146. }'}
payload = {'query': 'SELECT ?item  WHERE { ?item wdt:P31 wd:Q16521. }'}
headers = {'Accept': 'text/tab-separated-values'}

r = requests.post('https://query.wikidata.org/sparql',
				  data=payload, headers=headers)
taxons = set(re.findall(r'<http://www.wikidata.org/entity/(Q\d+)>', r.text))
for t in sorted([int(t[1:]) for t in taxons]):
    print('Q%d' % t)
