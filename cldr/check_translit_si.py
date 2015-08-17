# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Sinh:] [:Cf:]]')

PHONEMES = makePhonemeSet("""

    m n ɲ ŋ
    p b ᵐb ⁿd ʈ ɖ ⁿɖ k g ᵑg
    s ʃ
    t͡ʃ  d͡ʒ
    f h
    r r̩
    ʋ l j
    w

    i iː   u uː
    e eː ə o oː
    æː æ   a aː
    .

""")

check('si-si_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('si-si_FONIPA', GRAPHEMES, PHONEMES)
