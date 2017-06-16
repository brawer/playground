# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Latn:][:P:]]')

PHONEMES = makePhonemeSet("""

m m̥ n n̥ ŋ ŋ̊
p b d k ɡ
θ ð s t ʃ
f v h χ
{d͡ʒ}
r r̥
l ɬ
j w

i iː ɪ ɨ ɨː ɨ̞ ʊ u uː
ɛ eː oː ə ɔ ɔː
a ɑː
ˈ
""")

check('cy-fonipa-t-cy', GRAPHEMES, PHONEMES)
regtest('cy-fonipa-t-cy', GRAPHEMES, PHONEMES)
