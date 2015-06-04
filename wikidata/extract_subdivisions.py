import gzip, json

def get_values(item, property):
    claims = item.get('claims', {})
    values = claims.get(property)
    if not values: return []
    return [v.get('mainsnak', {}).get('datavalue', {}).get('value', '')
            for v in values]

def get_code(item):
    return '|'.join(get_values(item, 'P300'))

def get_mid(item):
    return '|'.join(get_values(item, 'P646'))

def normalize_language_tag(tag):
    parts = tag.split('-')
    if len(parts) == 1:
        return tag
    if len(parts[1]) == 4:
        parts[1] = parts[1].title()
    else:
        parts[1] = parts[1].upper()
    return '-'.join(parts)

def get_names(item):
    result = {}
    for v in item.get('labels', {}).values():
        result[normalize_language_tag(v['language'])] = v.get('value')
    return result

for line in gzip.open('/Users/sascha/src/wikidata/wikidata-20150525.json.gz'):
    line = line.strip()
    if len(line) < 5: continue
    if line.endswith(','): line = line[:-1]
    item = json.loads(line)
    id = item['id']
    code = get_code(item)
    if not code: continue
    mid = get_mid(item)
    names = get_names(item)
    for lang in sorted(list(names.keys())):
        name = names[lang]
        print '\t'.join([code, id, mid, lang, name]).encode('utf-8')






