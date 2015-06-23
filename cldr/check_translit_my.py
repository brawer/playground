# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

BURMESE_GRAPHEMES = icu.UnicodeSet()
BURMESE_GRAPHEMES.applyPattern('[:Mymr:]')

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

# TODO: Differences to JIPA, which we should resolve:
# - in JIPA, /ɴ/ is not in the phoneme list
# - in JIPA, /t͡ɕ/, /t͡ɕʰ/, and /d͡ʑ/ are /t͡ʃ/, /t͡ʃʰ/, and /d͡ʒ/
# - in JIPA, /ð/ is a phoneme (but none of our rules produce it)
# - in JIPA, /ɹ/ is a phoneme (but none of our rules produce it);
#   apparently it is used for loanwords of Pali origin.
#   Wikipedia says it's also used for English loanwords.
# - in JIPA, /w̥/ is /ʍ/
# - in JIPA, these are the vowels: /i/ /u/ /e/ /o/ /ə/ /ɛ/ /ɔ/ /a/
# - in JIPA, there are four tones: low /ma/, high /má/, creaky /ma̰/
#   and killed /maʔ/. In our rules, we currently have also /à/.
# - in JIPA, there are much fewer diphthongs. Are ours really phonemic?
#
# TODO: Can/should we emit syllable markers? /./

BURMESE_PHONEMES = makePhonemeSet("""

    m̥ m n̥ n ɲ̥ ɲ ŋ̊  ŋ ɴ
    p pʰ b t tʰ d t͡ɕ t͡ɕʰ d͡ʑ k kʰ g ʔ
    θ s sʰ z ʃ h
    w̥ w j
    l̥ l

    í ì ḭ
    ú ù ṵ
    ɪ ɪ́ ɪ̀ ɪ̰
    e é è ḛ
    ó ò o̰
    ə
    ɛ́ ɛ̰
    ɔ́ ɔ̀ ɔ̰
    æ
    a á à a̰

    eɪ̯ éɪ̯ èɪ̯ ḛɪ̯
    oʊ̯ óʊ̯ òʊ̯ o̰ʊ̯
    əʊ̯
    aɪ̯ áɪ̯ àɪ̯ a̰ɪ̯
    aʊ̯ áʊ̯ àʊ̯ a̰ʊ̯

""")

def match(s, unicodeset):
    return icu.UnicodeSet.span(
        unicodeset, s, icu.USetSpanCondition.SPAN_CONTAINED) == len(s)

def check(path):
    prefixes = {}
    num_lines = 0
    for line in codecs.open(path, 'r', 'utf-8'):
        num_lines += 1
        line = line.strip()
        if not line or line[0] == '#':
            continue
        assert line[-1] == ';'
        graph, arrow, phon = line[:-1].split()
        assert arrow == '→'
        if graph[:-1] in prefixes:
            error = ('%s:%d: %s hidden by %s, defined on line %d' %
                     (path, num_lines, graph, graph[:-1], prefixes[graph[:-1]]))
            print(error.encode('utf-8'))
        else:
            prefixes[graph] = num_lines
        if not match(graph, BURMESE_GRAPHEMES):
            print(('%s:%d: Non-Burmese graphemes in "%s"' %
                  (path, num_lines, line)).encode('utf-8'))
        if not match(phon, BURMESE_PHONEMES):
            print(('%s:%d: Non-Burmese phonemes in "%s"' %
                   (path, num_lines, line)).encode('utf-8'))

check('my-my_FONIPA.txt')

rules = codecs.open('my-my_FONIPA.txt', 'r', 'utf-8').read()
translit = icu.Transliterator.createFromRules(
    'my-my_FONIPA', rules, icu.UTransDirection.FORWARD)
