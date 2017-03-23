# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Tavt:]]')

PHONEMES = makePhonemeSet("""

p pʰ t d k kʰ ɡ ʔ
m n ɲ ŋ
f s h x
w j

t͡ɕ t͡ɕʷ t͡ɕʰ t͡ɕʰʷ

pʷ pʰʷ tʷ dʷ kʰʷ kʷ ɡʷ
mʷ nʷ ɲʷ ŋʷ
fʷ sʷ hʷ xʷ

i ɨ u
ɛ e ə ɔ o
a aː

iə̯ ɨə̯ uə̯
ai̯

˨ ˧˥ ˨˩ ˥ ˦ ˧˩

""")

#check('sat-sat_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('blt-blt_FONIPA', GRAPHEMES, PHONEMES)
