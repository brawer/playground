# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Ethi:]]')

PHONEMES = makePhonemeSet("""

    m n ɲ ŋ
    p pʼ b t tʼ d k kʼ ɡ ʔ
    f v s sʼ z ʃ ʒ ʕ h
    t͡ʃ t͡ʃʼ d͡ʒ
    r j l
    w

    i ɨ u
    e ə o
    a

    .

""")

check('am-am_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('am-am_FONIPA', GRAPHEMES, PHONEMES)
