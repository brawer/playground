# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, icu, os, re, unicodedata, urllib
import xml.etree.ElementTree as etree


LEXICON_URL = ('https://raw.githubusercontent.com/marytts/marytts-lexicon-de/'
               'master/modules/de/lexicon/')
CACHE_DIR = '/tmp/cache-lexicon-de'
LOCALE = icu.Locale('de')
COLLATOR = icu.Collator.createInstance(LOCALE)


def open_lexicon_file(filename):
    cache = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(cache):
        content = urllib.urlopen(LEXICON_URL + filename).read()
        with open(cache, 'w') as out:
            out.write(content)
    return open(cache, 'rb')


def read_lexicon():
    lex = []
    with open_lexicon_file('de.txt') as f:
        for line in f:
            try:
                line = line.split('#')[0].strip().decode('utf-8')
            except UnicodeDecodeError:
                continue
            columns = line.split()
            if len(columns) == 2:
                graph, phon = [col.strip() for col in columns]
                lex.append((graph, phon))
    return lex


def read_allophones():
    with open_lexicon_file('allophones.de.xml') as f:
        r = etree.parse(f).getroot()
    mapping = {'-': '.', "'": "ˈ", ",": "ˌ"}
    for element in (r.findall('./vowel') + r.findall('./consonant')):
        if 'ph' in element.attrib and 'ipa' in element.attrib:
            mapping[element.attrib['ph']] = element.attrib['ipa']
    return mapping


def _build_ipa_regexp(allophones):
    r = '|'.join(sorted(allophones.keys(), key=lambda x:(-len(x), x)))
    r = r.replace('\\', '\\\\').replace('{', '\\{').replace('?', '\\?')
    return re.compile('(%s|.)' % r)


def compare_entry(a, b):
    a = '\t'.join(a)
    b = '\t'.join(b)
    if COLLATOR.greater(a, b):
        return 1
    elif COLLATOR.greaterOrEqual(a, b):
        return 0
    else:
        return -1


if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    allophones = read_allophones()
    ipa_regexp = _build_ipa_regexp(allophones)
    def ipa(sampa):
        return ipa_regexp.sub(lambda x: allophones[x.group(1)], sampa)
    lex = [(word, ipa(sampa)) for word, sampa in read_lexicon()]
    lex.sort(cmp=compare_entry)
    print('\t'.join(['Form', 'Pronunciation']))
    print()
    print('# SPDX-License-Identifier: Unicode-DFS-2016')
    print()
    for word, pron in lex:
        print('\t'.join([word, pron]).encode('utf-8'))
