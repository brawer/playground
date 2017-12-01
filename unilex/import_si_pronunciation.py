# coding: utf-8
from __future__ import print_function, unicode_literals
import codecs, os, unicodedata, urllib
import icu

URL = ('https://raw.githubusercontent.com/googlei18n/language-resources/'
       'master/si/data/lexicon.tsv')

CACHED_PATH = '/tmp/lexicon-si.tsv'


def read_lexicon():
    lex = []
    if not os.path.exists(CACHED_PATH):
        content = urllib.urlopen(URL).read()
        with open(CACHED_PATH, 'w') as out:
            out.write(content)
    for line in codecs.open(CACHED_PATH, 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        sinhala, ipa = line.strip().split('\t')
        sinhala = unicodedata.normalize('NFC', sinhala)
        ipa = ipa.replace('y', 'j').replace('g', 'ɡ').replace(' ', '')
        lex.append('%s\t%s' % (sinhala, ipa))
    return lex


def print_lexicon(lex):
    print('# SPDX-License-Identifier: Unicode-DFS-2016')
    print('# Columns: Form; Pronunciation')
    print()
    collator = icu.Collator.createInstance(icu.Locale('si'))
    for line in sorted(lex, key=collator.getSortKey):
        print(line.encode('utf-8'))


print_lexicon(read_lexicon())

