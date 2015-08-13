# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Latn:] [:P:]]')

PHONEMES = makePhonemeSet("""

    m n
    p b d t k ɡ
    s z ʃ ʒ
    t͡s d͡z  t͡ʃ  d͡ʒ
    f x h
    r
    v l j

    i u
    e o
    a

    ui̯
    ei̯ eu̯ oi̯
    ai̯ au̯

""")

check('eo-eo_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('eo-eo_FONIPA', GRAPHEMES, PHONEMES)
