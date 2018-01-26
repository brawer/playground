# coding: utf-8

from __future__ import unicode_literals
import codecs, collections, icu, re, unicodedata


PHONEMES = '''
m n ɲ ŋ
p b t d k ɡ
f v ɾ s z h
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
$ipa_nasal = [m n ɲ ŋ];
$ipa_plosive = [p b t d k ɡ];
$ipa_fricative = [f v ɾ s z h];
$ipa_consonant = [$ipa_nasal $ipa_plosive $ipa_fricative l ʎ];
$ipa_affricate = [{t͡ʃ} {d͡ʒ} {d͡z}];
$ipa_vowel = [i u e {e̯} o ɛ ɔ a];
$onset = [
  j w $ipa_consonant $ipa_affricate
  {mj} {mw} {nj} {nw}
  {ps} {pɾ} {pɾw} {pl} {pw} {bɾ} {bɾw} {bl} {bw}
  {ts} {tɾ} {tɾw} {tl} {tw} {dɾ} {dɾw} {dl} {dw}
  {kɾ} {kw} {kɾw} {kl} {kw} {ɡɾ} {ɡɾw} {ɡl} {ɡw}
  {fɾ} {fl} {fw} {fɾw} {vɾ} {vw} {ɾw}
  {zm} {zn} {zɲ} {zl}
  {zb} {zbɾ} {zbw} {zd} {zdɾ} {zdw} {zɡ} {zɡɾ} {zɡw} {zv} {zvɾ} {zɾ} {zd͡ʒ} {zw}
  {sp} {spɾ} {spw} {st} {stɾ} {stw} {sk} {skɾ} {skw} {sf} {sfɾ} {sɾ} {st͡ʃ} {sw}
  {lw}
];

::Lower;
::NFC;

([abefhijklmoptvw]) → $1;
[á à] → ˈa;
{c [$ei \' ’]} $vowel → t͡ʃ;
c [éè] [\' ’]? → t͡ʃˈe;
c e [\' ’]? → t͡ʃe;
c [íì] [\' ’]? → t͡ʃˈi;
c i [\' ’]? → t͡ʃi;
[c {ch} k q {qu}] → k;
é → ˈe;
è → ˈɛ;
{g l $ei} $vowel → ʎ;
g l → ʎ;
ġ → d͡ʒ;
{g} $ei → d͡ʒ;
gn → ɲ;
[g {gh}] → ɡ;
[í ì] → ˈi;
ł → ɰ;
ṅ → ŋ;
ñ → ɲ;
nj → ɲ;
ó → ˈo;
ò → ˈɔ;
r → ɾ;
[ṡ x z] → z;
{s}[bdg] → z;
š → ʃ;
s → s;
{u} $vowel → w;
[ú ù] → ˈu;
u → u;
y → j;
ž → ʒ;
[ż đ {dh}] → d͡z;
d → d;
[[:P:][:Z:]]+ → ' ';
::NULL;

{n} [p b t d k ɡ f v ɾ s z $boundary] → ŋ;
{ɰ} ˈ? [ei] → ;
eɰ → e;
iɰ → i;
ɰ → e̯;
::NULL;

# Move stress marker before syllable onset: [zɡɾaŋfiɲˈae] → [zɡɾaŋfiˈɲae]
($onset) ˈ → ˈ $1;
::NULL;
'''


def make_transliterator():
    assert unicodedata.normalize(
        'NFC', IPA_TRANSLIT_RULES) == IPA_TRANSLIT_RULES
    return icu.Transliterator.createFromRules(
        'vec-vec_FONIPA', IPA_TRANSLIT_RULES, icu.UTransDirection.FORWARD)


def make_phoneme_set(s):
    pat = [u'\\u0020', "ˈ"]
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


def _build_split_regexps():
    onsets = list('''
        j w
        m n ɲ ŋ
        p b t d k ɡ
        f v ɾ s z h
        l ʎ  t͡ʃ d͡ʒ d͡z
        mj mw nj nw
        ps pɾ pɾw pl pw bɾ bɾw bw bl
        ts tɾ tɾw tl tw dɾ dɾw dw dl
        kɾ kw kɾw kl kw ɡɾ ɡɾw ɡw ɡl
        fɾ fl fw fɾw vɾ vw ɾw
        zm zn zɲ zl
        zb zbɾ zbw zd zdɾ zdw zɡ zɡɾ zɡw zv zvɾ zɾ zd͡ʒ zw
        sp spɾ spw st stɾ stw sk skɾ skw sf sfɾ sɾ st͡ʃ sw
        lw e̯
    '''.split())
    onsets.sort(key=len, reverse=True)
    vowels = list('i u e o ɛ ɔ a'.split())
    vowels.sort(key=len, reverse=True)
    return re.compile('((%s)?(%s))' % ('|'.join(onsets), '|'.join(vowels)))

_onset_vowel = _build_split_regexps()


def stress(s):
    if "ˈ" in s or len(s) == 1:
        return s
    syll = _onset_vowel.sub(lambda m: "." + m.group(0), s)
    if syll[0] != '.':
        return s
    syll = [s for s in syll.split('.') if s]
    if len(syll) == 1:
        return s
    pos = -2
    if syll[-1].endswith('oŋ') or syll[-1].endswith('aɾ'):
        pos = -1
    return ''.join(syll[:pos] + ["ˈ"] + syll[pos:])


if __name__ == '__main__':
    onsets = collections.Counter()
    translit = make_transliterator()
    phonemes = make_phoneme_set(PHONEMES)
    print('Count\tForm\tPronunciation\n')
    print('# SPDX-License-Identifier: Unicode-DFS-2016\n')
    for line in codecs.open('data/vec/frequency.txt', 'r', 'utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        count, form = line.split('\t')
        count = int(count)
        form = unicodedata.normalize('NFC', form)
        ipa = ' '.join(stress(w) for w in translit.transliterate(form).split())
        print('\t'.join((str(count), form, ipa)).encode('utf-8'))
        assert match(ipa, phonemes), ipa.encode('utf-8')
        onset = re.split(r'i|u|e|o|ɛ|ɔ|a', ipa.split()[-1])[0]
        if onset:
            onsets[onset] += 1
    #for ipa, count in onsets.most_common():
        #print '\t'.join([ipa, str(count)]).encode('utf-8')
