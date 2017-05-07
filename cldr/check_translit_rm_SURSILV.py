# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Latn:]]')

PHONEMES = makePhonemeSet("""

    m n ɲ
    p b t d c ɟ k g
    f v s z ʃ ʒ h
    t͡ʃ t͡s
    r l j ʎ
    w

    i u e ʊ ɛ ɔ a
    ɪa̯ ɪa̯ʊ̯ ɪʊ̯ ɪɛ̯ u ʊa̯ ʊa̯ʊ̯ ʊɛ̯ ʊɛ̯ɪ̯ ʊɔ̯
    ɛɪ̯ ɛʊ̯ aɪ̯ aʊ̯

""")

check('rm-fonipa-sursilv-t-rm-sursilv', GRAPHEMES, PHONEMES)
regtest('rm-fonipa-sursilv-t-rm-sursilv', GRAPHEMES, PHONEMES)
