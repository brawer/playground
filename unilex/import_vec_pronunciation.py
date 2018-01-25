# coding: utf-8

from __future__ import unicode_literals
import codecs, icu, unicodedata


PHONEMES = '''
m n ɲ ŋ
p b t d k ɡ h
f v ɾ s z
l ʎ j w
t͡ʃ d͡ʒ d͡z
i u e e̯ o ɛ ɔ a
'''

IPA_TRANSLIT_RULES = '''
# References
# ----------
# [1] https://en.wikipedia.org/wiki/Venetian_language#Phonology
# [2] https://en.wikipedia.org/wiki/Help:IPA/Venetian
#
# Output phonemes
# ---------------

$boundary = [^[:L:][:M:][:N:]];
$e = [e é è];
$i = [i í ì];
$ei = [$e $i];
$vowel = [a á à $ei o ó ò u ú ù];

[[:P:][:Z:]]+ → ' ';
::Lower;
::NFC;
([abefhijklmoptvw]) → $1;
[á à] → a;
{c [$ei \' ’]} $vowel → t͡ʃ;
c $e [\' ’]? → t͡ʃe;
c $i [\' ’]? → t͡ʃi;
[c {ch} k q {qu}] → k;
é → e;
è → ɛ;
{g l $ei} $vowel → ʎ;
g l → ʎ;
ġ → d͡ʒ;
g $ei → d͡ʒ;
gn → ɲ;
[g {gh}] → ɡ;
[í ì] → i;
ł → ɰ;
ṅ → ŋ;
ñ → ɲ;
nj → ɲ;
ó → o;
ò → ɔ;
r → ɾ;
[ṡ x z] → z;
{s}[bdg] → z;
š → ʃ;
s → s;
{u} $vowel → w;
[u ú ù] → u;
y → j;
ž → ʒ;
[ż đ {dh}] → d͡z;
d → d;
[\- \' ’] → ;

::NULL;
{n} [p b t d k ɡ f v ɾ s z $boundary] → ŋ;
ɰe → e;
ɰi → i;
eɰ → e;
iɰ → i;
ɰ → e̯;
'''


def make_transliterator():
    assert unicodedata.normalize(
        'NFC', IPA_TRANSLIT_RULES) == IPA_TRANSLIT_RULES
    return icu.Transliterator.createFromRules(
        'vec-vec_FONIPA', IPA_TRANSLIT_RULES, icu.UTransDirection.FORWARD)


def make_phoneme_set(s):
    pat = [u'\\u0020']
    for phoneme in s.split():
        if len(phoneme) == 1:
            pat.append(phoneme)
        else:
            pat.append('{%s}' % phoneme)
    result = icu.UnicodeSet()
    result.applyPattern('[%s]' % ' '.join(pat))
    return result


def match(s, unicodeset):
    return icu.UnicodeSet.span(
        unicodeset, s, icu.USetSpanCondition.SPAN_CONTAINED) == len(s)


if __name__ == '__main__':
    translit = make_transliterator()
    phonemes = make_phoneme_set(PHONEMES)
    print('Count\tForm\tPronunciation\n')
    print('# SPDX-License-Identifier: Unicode-DFS-2016\n')
    for line in codecs.open('data/vec/frequency.txt', 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        count, form = line.split('\t')
        if form in {'ʣ', 'ǌ', 'ʦ'}:
            continue
        count = int(count)
        form = unicodedata.normalize('NFC', form)
        ipa = translit.transliterate(form)
        print('\t'.join((str(count), form, ipa)).encode('utf-8'))
        assert match(ipa, phonemes), ipa.encode('utf-8')
