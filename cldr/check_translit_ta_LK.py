# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Taml:] [:P:]]')

PHONEMES = makePhonemeSet("""

    m n ɲ ɳ ŋ
    p b tʳ t̪ d̪ ʈ ɖ k ɡ
    f s ʂ sʼ ʃ h x
    ʋ r ɻ l ɭ j

    t͡ʃ d͡ʒ

    i iː u uː
    e eː o oː
    a aː

    aɪ̯ aʊ̯


""")

check('ta-LK-fonipa-t-ta-LK', GRAPHEMES, PHONEMES)
regtest('ta-LK-fonipa-t-ta-LK', GRAPHEMES, PHONEMES)
