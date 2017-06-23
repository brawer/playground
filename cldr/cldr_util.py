# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu
import re
import unicodedata


def makePhonemeSet(s):
    pat = []
    for phoneme in s.split():
        if len(phoneme) == 1:
            pat.append(phoneme)
        else:
            pat.append('{%s}' % phoneme)
    print ' '.join(pat).encode('utf-8')
    result = icu.UnicodeSet()
    result.applyPattern('[%s]' % ' '.join(pat))
    return result


def match(s, unicodeset):
    return icu.UnicodeSet.span(
        unicodeset, s, icu.USetSpanCondition.SPAN_CONTAINED) == len(s)


WHITELISTED_SPECIAL_RULES = [
    "{\.} [:^Letter:] → ;",
    "\\u200C → ;",
    "\\u200D → ;",

    # am-am_FONIPA
    "\\u135D → '';",
    "\\u135E → '';",
    "\\u135F → '';",
    "{i} [[:L:]] → i \\.;",
    "{ɨ} [[:L:]] → ɨ \\.;",
    "{u} [[:L:]] → u \\.;",
    "{e} [[:L:]] → e \\.;",
    "{o} [[:L:]] → o \\.;",
    "{ə} [[:L:]] → ə \\.;",
    "{a} [[:L:]] → a \\.;",

    # fa-fa_FONIPA
    "ي → ی;",
    "ى → ی;",
    "ك → ک;",
    "ە → ه;",

    # ia-ia_FONIPA
    "{age} $end_of_word → ad͡ʒe;",
    "{agi} $vowel → ad͡ʒ;",
    "{egi} $vowel → ed͡ʒ;",

    # sat-sat_FONIPA
    "ᱹᱸ → ᱺ ;",
    "ᱸᱹ → ᱺ ;",
    "ᱻᱹ → ᱹᱻ ;",
    "ᱻᱸ → ᱸᱻ ;",
    "ᱻᱺ → ᱺᱻ ;",
    "ᱼᱹ → ᱹᱼ ;",
    "ᱼᱸ → ᱸᱼ ;",
    "ᱼᱺ → ᱺᱼ ;",

    # si-si_FONIPA
    "k { ə } [rl] u    → a;",

    # ta-ta_FONIPA
    "\\u0BCD → ;",    
]


def check_nfc(path):
    with codecs.open(path, 'r', 'utf-8') as f:
        text = f.read()
    if text != unicodedata.normalize('NFC', text):
        print('%s: Not in normalization form NFC' % path)


def check(path, graphemes, phonemes):
    prefixes = {}
    num_lines = 0
    for line in codecs.open('rules/%s.txt' % path, 'r', 'utf-8'):
        num_lines += 1
        line = line.split('#')[0].strip()
        if not line or line[0] in ':$[' or '$' in line:
            continue
        if line[-1] != ';':
            error = '%s:%d: line should end in ;' % (path, num_lines)
            print(error.encode('utf-8'))
            continue
        if line in WHITELISTED_SPECIAL_RULES:
            continue
        line = line.replace('\\.', '.').replace("''", "")
        line = re.sub(r'\\u([0-9a-fA-F]{4})',
                      lambda m: unichr(int(m.group(1), 16)),
                      line)
        line =  line.replace("' '", "\\u0020")
        graph, phon = line[:-1].split('→')
        graph, phon = graph.strip(), phon.strip()
        for g in '{}[] ': graph = graph.replace(g, '')
        for p in '. ': phon = phon.replace(p, '')
        if graph[:-1] in prefixes:
            error = ('%s:%d: %s hidden by %s, defined on line %d' %
                     (path, num_lines, graph, graph[:-1], prefixes[graph[:-1]]))
            print(error.encode('utf-8'))
        else:
            prefixes[graph] = num_lines
        if not match(graph, graphemes):
            print(('%s:%d: Unexpected graphemes in "%s"' %
                  (path, num_lines, line)).encode('utf-8'))
        if not match(phon, phonemes) and phon not in ['\\u0020']:
            print(('%s:%d: Unexpected phonemes in "%s"' %
                   (path, num_lines, line)).encode('utf-8'))


def regtest(translit_name, graphemes, phonemes):
    check_nfc('rules/%s.txt' % translit_name)
    rules = codecs.open('rules/%s.txt' % translit_name, 'r', 'utf-8').read()
    translit = icu.Transliterator.createFromRules(
        translit_name, rules, icu.UTransDirection.FORWARD)
    num_lines = 0
    test_path = 'test/%s.txt' % translit_name
    check_nfc(test_path)
    for line in codecs.open(test_path, 'r', 'utf-8'):
        num_lines += 1
        if not line.strip() or line.startswith('#'):
            continue
        try:
            graph, expected_ipa = line.strip().split('\t')
        except ValueError:
            print(('%s:%d: Invalid testcase format "%s"' %
                   (test_path, num_lines, line.strip())).encode('utf-8'))
            continue
        if False:
            actual_ipa = translit.transliterate(graph).strip()
            print((u'%s\t%s' % (graph.strip(), actual_ipa)).encode('utf-8'))
            continue
        if not match(graph, graphemes):
            print(('%s:%d: Unexpected graphemes in "%s"' %
                  (test_path, num_lines, graph)).encode('utf-8'))
        if not match(expected_ipa, phonemes):
            print(('%s:%d: Unexpected phonemes in "%s"' %
                   (test_path, num_lines, expected_ipa)).encode('utf-8'))
        actual_ipa = translit.transliterate(graph)
        if actual_ipa != expected_ipa:
            print(('%s:%d: Expected "%s" but got "%s" for "%s"' %
                   (test_path, num_lines,
                    expected_ipa, actual_ipa, graph)).encode('utf-8'))
