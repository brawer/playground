import json

def get_code(item):
    claims = item.get('claims', {})
    code = claims.get('P300')
    if not code: return None
    return '|'.join([c.get('mainsnak', {}).get('datavalue', {}).get('value', '')
                     for c in code])

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

for line in open('x'):
    line = line.strip()
    if line.endswith(','): line = line[:-1]
    item = json.loads(line)
    id = item['id']
    code = get_code(item)
    if not code: continue
    names = get_names(item)
    for lang in sorted(list(names.keys())):
        name = names[lang]
        print '\t'.join([code, id, lang, name]).encode('utf-8')






