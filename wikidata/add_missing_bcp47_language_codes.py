# Script for generating Wikidata QuickStatements to add missing
# IETF BCP 47 codes for langauges in the IETF language subtag registry.
# Output is pasted into: https://tools.wmflabs.org/quickstatements

from SPARQLWrapper import SPARQLWrapper, JSON
import datetime, icu, re


def generate_quickstatements(registry):
    s = SPARQLWrapper("https://query.wikidata.org/sparql")
    s.setQuery("""SELECT ?item ?itemLabel ?ISO_639_3 ?ISO_639_1 ?bcp WHERE {
        ?item wdt:P220 ?ISO_639_3.
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        OPTIONAL { ?item wdt:P305 ?bcp. }
        OPTIONAL { ?item wdt:P218 ?ISO_639_1. }
        }
        """)
    s.setReturnFormat(JSON)
    results = s.query().convert()
    for e in results["results"]["bindings"]:
        id = e["item"]["value"].split('/')[-1]
        bcp = e.get("bcp", {}).get("value")
        iso639_1 = e.get("ISO_639_1", {}).get("value")
        iso639_3 = e.get("ISO_639_3", {}).get("value")
        loc = icu.Locale(bcp if bcp else iso639_3)
        minloc = str(loc.minimizeSubtags())
        if not bcp and len(minloc) == 2:
            continue
        if bcp and bcp != minloc:
            continue
        if bcp and bcp not in (iso639_1, iso639_3):
            continue
        if bcp:
            continue
        if minloc not in registry or minloc == 'und':
            continue
        added, deprecated, name = registry[minloc]
        qs = [id, 'P305', '"%s"' % minloc]
        qs.extend(['P580', '+%sT00:00:00Z/11' % added])
        if deprecated:  # deprecated on date D --> valid until (D - 1)
            d = datetime.date.fromisoformat(deprecated)
            dep = datetime.date.fromordinal(d.toordinal() - 1).isoformat()[:10]
            qs.extend(['P582', '+%sT00:00:00Z/11' % dep])
        qs.extend([
              'S248', 'Q57271947',  # IANA language subtag registry
              'S813', '+2019-02-08T00:00:00Z/11',
              'S577', '+%sT00:00:00Z/11' % added, 
              'S1476', 'en:"%s"' % name,
              '/* Add missing IETF language codes */'])
        print('\t'.join(qs))


def read_registry(path):
    reg = {}
    with open(path) as f:
        for entry in f.read().split('%%'):
            if 'Type: language' not in entry: continue
            tag = re.search(r'Subtag: ([a-z]{2,3})', entry).group(1)
            name = re.search(r'Description: (.+)', entry).group(1)
            name = name.strip().replace("'", "’")
            added = re.search(r'Added: (\d{4}-\d{2}-\d{2})', entry).group(1)
            deprecated = re.search(r'Deprecated: (\d{4}-\d{2}-\d{2})', entry)
            if deprecated: deprecated = deprecated.group(1)
            reg[tag] = (added, deprecated, name)
    return reg


if __name__ == '__main__':
    registry = read_registry('language-subtag-registry')
    generate_quickstatements(registry)
