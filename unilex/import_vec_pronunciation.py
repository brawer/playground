# coding: utf-8

from __future__ import unicode_literals
import codecs, icu, unicodedata


IPA_TRANSLIT_RULES = '''
# References
# ----------
# [1] https://en.wikipedia.org/wiki/Venetian_language#Phonology
# [2] https://en.wikipedia.org/wiki/Help:IPA/Venetian

$boundary = [^[:L:][:M:][:N:]];
$e = [e é è];
$i = [i í ì];
$ei = [$e $i];
$vowel = [a á à $ei o ó ò u ú ù];

::Lower;
::NFC;
([abefhijklmnoptvw]) → $1;
[á à] → a;
{c [$ei \' ’]} $vowel → t͡ʃ;
c $e [\' ’]? → t͡ʃe;
c $i [\' ’]? → t͡ʃi;
[c {ch} k q {qu}] → k;
é → e;
è → ɛ;
gl $ei? → ʎ;
ġ → d͡ʒ;
g $ei → d͡ʒ;
gn → ɲ;
[g {gh}] → ɡ;
[í ì] → i;
ł → ɰ;
ṅ → ŋ;
ñ → ɲ;
::NULL;
{n} [pk] → ŋ;
ó → o;
ò → ɔ;
r → ɾ;
[ṡ x] → z;
{s}[bdg] → z;
š → ʃ;
s → s;
{u} $vowel → w;
[u ú ù] → u;
ž → ʒ;
[ż đ {dh}] → d͡z;
d → d;
$boundary {z} → d͡z;
z → z;
[\- \' ’] → ;

::NULL;
{n} [p b t d k ɡ f v ɾ s z $boundary] → ŋ;
ɰe → e;
ɰi → i;
eɰ → e;
iɰ → i;

::NULL;
ɰ → e̯;

'''


def make_transliterator():
    assert unicodedata.normalize(
        'NFC', IPA_TRANSLIT_RULES) == IPA_TRANSLIT_RULES
    return icu.Transliterator.createFromRules(
        'vec-vec_FONIPA', IPA_TRANSLIT_RULES, icu.UTransDirection.FORWARD)


if __name__ == '__main__':
    translit = make_transliterator()
    print('Count\tForm\tPronunciation\n')
    print('# SPDX-License-Identifier: Unicode-DFS-2016\n')
    for line in codecs.open('data/vec/frequency.txt', 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        count, form = line.split('\t')
        count = int(count)
        form = unicodedata.normalize('NFC', form)
        ipa = translit.transliterate(form)
        print('\t'.join((str(count), form, ipa)).encode('utf-8'))


