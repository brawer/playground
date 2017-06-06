# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Arab:] \u064e  ٰ  ْ  ِ  ُ  ٓ \u200c \u200d]')

PHONEMES = makePhonemeSet("""

    m n
    p b t d k ɡ ʔ
    f v s z ʃ ʒ ʁ ɢ h χ
    t͡ʃ d͡ʒ
    l ɾ j w
    iː uː e o æ ɒː

""")

check('fa-fonipa-t-fa', GRAPHEMES, PHONEMES)
regtest('fa-fonipa-t-fa', GRAPHEMES, PHONEMES)
