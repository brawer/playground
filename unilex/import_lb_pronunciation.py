# coding: utf-8
from __future__ import print_function, unicode_literals
import codecs, icu, os, re, unicodedata, urllib
import xml.etree.ElementTree as etree


LEXICON_URL = ('https://raw.githubusercontent.com/marytts/marytts-lexicon-lb/'
               'master/modules/lb/lexicon/')
WORDCOUNT_URL = 'http://www.gstatic.com/i18n/corpora/wordcounts/lb.txt'
CACHE_DIR = '/tmp/cache-lexicon-lb'
LOCALE = icu.Locale('lb')
COLLATOR = icu.Collator.createInstance(LOCALE)


def get_allophones():
    mapping = {'ts': 't͡s', 'ts\\': 't͡ɕ', 'i6': 'iɐ̯', '3I': 'ɜɪ̯'}
    cache = os.path.join(CACHE_DIR, 'allophones.xml')
    if not os.path.exists(cache):
        content = urllib.urlopen(LEXICON_URL + 'allophones.lb.xml').read()
        with open(cache, 'w') as out:
            out.write(content)
    r = etree.parse(cache).getroot()
    for element in (r.findall('./vowel') + r.findall('./consonant')):
        if 'ph' in element.attrib and 'ipa' in element.attrib:
            mapping[element.attrib['ph']] = element.attrib['ipa']
    return mapping


def get_wordcounts():
    counts = {}
    cache = os.path.join(CACHE_DIR, 'wordcounts.txt')
    if not os.path.exists(cache):
        content = urllib.urlopen(WORDCOUNT_URL).read()
        with open(cache, 'w') as out:
            out.write(content)
    for line in codecs.open(cache, 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        count, word = line.split('\t')
        counts[word] = int(count)
    return counts


def compare_lb(a, b):
    a = '\t'.join(a)
    b = '\t'.join(b)
    if COLLATOR.greater(a, b):
        return 1
    elif COLLATOR.greaterOrEqual(a, b):
        return 0
    else:
        return -1


def read_lexicon():
    lex = []
    cache = os.path.join(CACHE_DIR, 'lexicon.txt')
    if not os.path.exists(cache):
        content = urllib.urlopen(LEXICON_URL + 'lb.txt').read()
        with open(cache, 'w') as out:
            out.write(content)
    for line in codecs.open(cache, 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        graph, phon = line.strip().split('\t')
        lex.append((graph, phon))
    return lex


if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    allophones = get_allophones()
    wordcounts = get_wordcounts()
    r = '|'.join(sorted(allophones.keys(), key=lambda x:(-len(x), x)))
    r = r.replace('\\', '\\\\').replace('{', '\\{').replace('?', '\\?')
    allophones_regexp = re.compile('(%s)' % r)
    def ipa(s):
        return allophones_regexp.sub(lambda x: allophones[x.group(1)], s)
    lex = []
    for graph, sampa in read_lexicon():
        if graph not in wordcounts:
            if graph.title() in wordcounts:
                graph = graph.title()
            elif graph.upper() in wordcounts:
                graph = graph.upper()
        lex.append((graph, ipa(sampa)))
    lex.sort(cmp=compare_lb)
    print('\t'.join(['Form', 'Pronunciation']))
    print()
    print('# SPDX-License-Identifier: Unicode-DFS-2016')
    print()
    for graph, phon in lex:
        print('\t'.join((graph, phon)).encode('utf-8'))
