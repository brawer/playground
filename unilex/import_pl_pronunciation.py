# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, icu, os, re, unicodedata, urllib
import xml.etree.ElementTree as etree


LEXICON_URL = ('https://raw.githubusercontent.com/brawer/marytts-lexicon-pl/'
               'master/modules/pl/lexicon/')
CACHE_DIR = '/tmp/cache-lexicon-pl'
LOCALE = icu.Locale('pl')
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
    with open_lexicon_file('pl.txt') as f:
        for line in f:
            line = line.decode('utf-8').split('#')[0]
            if not line:
                continue
            columns = line.split('\t')
            assert len(columns) == 2
            lex.append((columns[0].strip(), columns[1].strip()))
    return lex


def read_allophones():
    with open_lexicon_file('allophones.pl.xml') as f:
        r = etree.parse(f).getroot()
    mapping = {'.': '.'}
    for element in (r.findall('./vowel') + r.findall('./consonant')):
        if 'ph' in element.attrib and 'ipa' in element.attrib:
            mapping[element.attrib['ph']] = element.attrib['ipa']
    return mapping


def compare_entry(a, b):
    a = '\t'.join(a)
    b = '\t'.join(b)
    if COLLATOR.greater(a, b):
        return 1
    elif COLLATOR.greaterOrEqual(a, b):
        return 0
    else:
        return -1


def ipa(pseudosampa, allophones):
    ipa = ''.join([allophones[p] for p in pseudosampa.split()])
    syllables = []
    for syll in ipa.split('.'):
        if "ˈ" in syll:
            syll = "ˈ" + syll.replace("ˈ", "")
        syllables.append(syll)
    ipa = '.'.join(syllables)
    ipa = ipa.replace(".ˈ", "ˈ")
    ipa = ipa.replace('ɛw̃', 'ɛ̃')
    ipa = ipa.replace('ɔw̃', 'ɔ̃')
    ipa = ipa.replace('ʲj', 'j')  # brakiem /ˈbra.kʲjɛm/ --> /ˈbra.kjɛm/
    ipa = unicodedata.normalize('NFC', ipa)
    return ipa


if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    allophones = read_allophones()
    lex = [(word, ipa(pseudosampa, allophones))
           for word, pseudosampa in read_lexicon()]
    lex.sort(cmp=compare_entry)
    print('\t'.join(['Form', 'Pronunciation']))
    print()
    print('# SPDX-License-Identifier: Unicode-DFS-2016')
    print()
    for word, pron in lex:
        print('\t'.join([word, pron]).encode('utf-8'))
