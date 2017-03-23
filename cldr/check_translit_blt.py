# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Tavt:]]')

PHONEMES = makePhonemeSet("""

t tʷ d dʷ k kʷ
n nʷ ɲ ŋ
s x
w

i ɨ ɛ
ə o
a

ɨə̯ ai̯

˨ ˧˥ ˨˩ ˥ ˦ ˧˩

""")

#check('sat-sat_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('blt-blt_FONIPA', GRAPHEMES, PHONEMES)
