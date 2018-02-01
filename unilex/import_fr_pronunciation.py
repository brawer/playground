# coding: utf-8

from __future__ import unicode_literals
import codecs, os, re, unicodedata
import xml.etree.ElementTree as etree


_MARYTTS_LEXICON_FR = '../../marytts-lexicon-fr/modules/fr/lexicon'


def read_allophones(f):
    mapping = {'-': '.', "'": "ˈ", ",": "ˌ"}
    r = etree.parse(f).getroot()
    for element in (r.findall('./vowel') + r.findall('./consonant')):
        if 'ph' in element.attrib and 'ipa' in element.attrib:
            ipa = unicode(element.attrib['ipa'])
            assert unicodedata.normalize('NFC', ipa.strip()) == ipa
            mapping[element.attrib['ph']] = ipa
    return mapping


def _build_ipa_regexp(allophones):
    r = '|'.join(sorted(allophones.keys(), key=lambda x:(-len(x), x)))
    r = r.replace('\\', '\\\\').replace('{', '\\{').replace('?', '\\?')
    return re.compile('(%s|.)' % r)


with open(_MARYTTS_LEXICON_FR + '/allophones.fr.xml', 'rb') as f:
    _allophones = read_allophones(f)
    _ipa_regexp = _build_ipa_regexp(_allophones)


def ipa(xsampa):
    return _ipa_regexp.sub(lambda x: _allophones[x.group(1)], xsampa)


if __name__ == '__main__':
    for line in codecs.open(_MARYTTS_LEXICON_FR + '/fr.txt', 'rb', 'utf-8'):
        line = line.strip()
        if not line or line[0] == '#':
            continue
        columns = [c.strip() for c in line.split()]
        if len(columns) < 2:
            continue
        word, sampa = columns[:2]
        print '\t'.join([word, ipa(sampa)]).encode('utf-8')
