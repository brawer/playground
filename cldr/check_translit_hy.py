# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

rules = codecs.open('hy-hy_FONIPA.txt', 'r', 'utf-8').read()
translit = icu.Transliterator.createFromRules(
    "hy-hy_FONIPA", rules, icu.UTransDirection.FORWARD)

def makePhonemeSet(s):
    pat = []
    for phoneme in s.split():
        if len(phoneme) == 1:
            pat.append(phoneme)
        else:
            pat.append('{%s}' % phoneme)
    #print ' '.join(pat).encode('utf-8')
    result = icu.UnicodeSet()
    result.applyPattern('[%s]' % ' '.join(pat))
    return result

ARMENIAN_GRAPHEMES = icu.UnicodeSet()
ARMENIAN_GRAPHEMES.applyPattern('[:Armn:]')

ARMENIAN_PHONEMES = makePhonemeSet("""

    m n
    p pʰ t tʰ k kʰ b d g 
    t͡s t͡sʰ t͡ʃ t͡ʃʰ d͡z d͡ʒ
    f v s z ʃ ʒ x ɣ h
    l j r ɾ

    i u
    ɛ ə o
    a

""")

def match(s, unicodeset):
    return icu.UnicodeSet.span(
        unicodeset, s, icu.USetSpanCondition.SPAN_CONTAINED) == len(s)

def check(testdatapath):
    num_lines = 0
    for line in codecs.open(testdatapath, 'r', 'utf-8'):
        num_lines += 1
        line = line.strip()
        if not line or line[0] == '#':
            continue
        graph, expected_phon = line.split('\t')
        if not match(graph, ARMENIAN_GRAPHEMES):
            print(('%s:%d: Non-Armenian graphemes in "%s"' %
                   (testdatapath, num_lines, graph)).encode('utf-8'))
        if not match(expected_phon, ARMENIAN_PHONEMES):
            print(('%s:%d: Non-Armenian phonemes in "%s"' %
                   (testdatapath, num_lines, expected_phon)).encode('utf-8'))
        actual_phon = translit.transliterate(graph)
        if expected_phon != actual_phon:
            print(('%s:%d: Expected %s → %s, got %s' %
                   (testdatapath, num_lines,
                    graph, expected_phon, actual_phon)).encode('utf-8'))

check('test-hy-hy_FONIPA.txt')
