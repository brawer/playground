from __future__ import unicode_literals
import bz2, json, subprocess

def read_wikidata_dump(path):
    # On Mac OS X 10.11.2, module bz2 fails on wikidata-20151221-all.json.bz2,
    # so we let /usr/bin/bzip2 do the decompression.
    proc = subprocess.Popen(['/usr/bin/bzip2', '-cd', path],
                            stdout=subprocess.PIPE, bufsize=256*1024)
    while True:
        line = proc.stdout.readline().strip()
        if not line: return
        if len(line) < 10: continue
        if line[-1] == ',': line = line[:-1]
        yield json.loads(line, encoding="utf-8")


def normalize_language_tag(tag):
    parts = tag.split('-')
    if len(parts) == 1:
        return tag
    if len(parts[1]) == 4:
        parts[1] = parts[1].title()
    else:
        parts[1] = parts[1].upper()
    return '-'.join(parts)

def has_property(item, property):
    claims = item.get('claims', {})
    if claims.get(property):
        return True
    else:
        return False
    
def get_names(item):
    result = {}
    for v in item.get('labels', {}).values():
        result[normalize_language_tag(v['language'])] = v.get('value')
    return result

def get_classes(item):
    return({v['numeric-id'] for v in get_values(item, 'P31')})

def get_values(item, property):
    claims = item.get('claims', {})
    values = claims.get(property)
    if not values: return []
    return [v.get('mainsnak', {}).get('datavalue', {}).get('value', '')
            for v in values]

def get_entities(item, property):
    s = set()
    for entity in get_values(item, property):
        if entity:
            id = entity.get('numeric-id')
            if id is not None and entity.get('entity-type') == 'item':
                s.add('Q%s' % id)
    return s


def get_original_language(item):
    countries = get_entities(item, 'P17')
    classes = get_entities(item, 'P31')
    #has_geonames_id = has_property(item, 'P1566')
    if set.intersection(classes, {'Q515', 'Q5119', 'Q15284', 'Q747074', 'Q498162', 'Q484170', 'Q11618417', 'Q253019', 'Q486972', 'Q2983893'}):
        # Q21:England, Q30:US, Q145:UK
        if set.intersection(countries, {'Q21', 'Q30', 'Q145'}):
            return 'en'
        if set.intersection(countries, {'Q142'}):  # France
            return 'fr'
        if set.intersection(countries, {'Q183'}):  # Germany
            return 'de'
        if set.intersection(countries, {'Q55'}):  # Netherlands
            return 'nl'
        if set.intersection(countries, {'Q213'}):  # Czech Republic
            return 'cs'
        if set.intersection(countries, {'Q38'}):  # Italy
            return 'it'
        if set.intersection(countries, {'Q17'}):  # Japan
            return 'ja'
        if set.intersection(countries, {'Q148'}):  # China
            return 'zh'
        if set.intersection(countries, {'Q45'}):  # Portugal
            return 'pt'
        if set.intersection(countries, {'Q155'}):  # Brazil
            return 'pt-BR'
        if set.intersection(countries, {'Q159'}):  # Russia
            return 'ru'
        if set.intersection(countries, {'Q29'}):  # Spain
            return 'es'
        # Q96:Mexico, Q414:Argentinia, Q736:Ecuador, Q750:Bolivia
        if set.intersection(countries, {'Q96', 'Q414', 'Q736', 'Q750'}):
            return 'es-419'
    if get_values(item, 'P843'):  # GeoID in Romania
        return 'ro'


def get_population(item):
    pop = 0
    for value in get_values(item, 'P1082'):
        try:
            pop = max(int(value.get('amount', 0)), pop)
        except ValueError:
            pass
    return pop
