# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Cyrl:]]')

# TODO(sascha): Verify whether /lʲ/ is really phonemic in Kyrgyz;
# is there really a minimal pair with /l/ versus /lʲ/?
#
# TODO(sascha): No gemination for /p b g q z ʃ f v r/? No long /ɯː/?
PHONEMES = makePhonemeSet("""

    m mː n nː ŋ
    p b t tː d dː k kː ɡ q
    t͡s t͡ʃ d͡ʒ
    s sː z ʃ
    f v j χ ʁ
    r l lː lʲ

    i iː y yː ɯ u uː
    e eː o oː
    ø øː
    ɑ ɑː

    .

""")

check('ky-ky_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('ky-ky_FONIPA', GRAPHEMES, PHONEMES)
