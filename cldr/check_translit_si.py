# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Sinh:] [:Cf:]]')

# TODO: ᵑɡ or ⁿɡ ?
# TODO: No  t͡ʃ  d͡ʒ ?
# TODO: No əː ?
PHONEMES = makePhonemeSet("""

    m n ɲ ŋ
    p b ᵐb ⁿd d t ʈ ɖ ⁿɖ k ɡ ⁿɡ
    s ʃ
    c ɟ
    f h
    r
    l j
    w

    i iː   u uː
    e eː ə o oː
    æː æ   a aː
    ei̯ ou̯ ou̯ː
    æi̯ ai̯ au̯
    .

""")

check('si-si_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('si-si_FONIPA', GRAPHEMES, PHONEMES)
