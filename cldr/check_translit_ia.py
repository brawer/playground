# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Latn:]]')

PHONEMES = makePhonemeSet("""

    m n ŋ
    p b t d k ɡ
    f v s z ʃ ʒ h
    t͡s d͡ʒ
    ɾ l j w

    i u
    e o
    a

    ei̯ eu̯ oi̯
    ai̯ au̯

    .

""")

check('ia-fonipa-t-ia', GRAPHEMES, PHONEMES)
regtest('ia-fonipa-t-ia', GRAPHEMES, PHONEMES)
