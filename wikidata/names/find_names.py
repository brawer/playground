from __future__ import unicode_literals
import tools, json, sys

path = 'wikidata-20151221-all.json.bz2'
print("#population\tid\tlang\tname")
for item in tools.read_wikidata_dump(path):
    lang = tools.get_original_language(item)
    if lang:
        names = tools.get_names(item)
        if lang in names:
            id = item['id']
            pop = tools.get_population(item)
            line = '\t'.join([str(pop), id, lang, names[lang]])
            print line.encode('utf-8')
            sys.stdout.flush()
