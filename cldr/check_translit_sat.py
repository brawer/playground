# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Olck:]]')

# TODO: This phoneme set seems a little large.
# Collect a large corpus, and see which ones actually occur.
# TODO: Is /ɽː/ physiologically possible?
PHONEMES = makePhonemeSet("""

    m mː n nː ɳ ɳː ɲ ɲː ŋ ŋː
    p pʰ pʼ b bʰ t tʰ tʼ d dʰ ʈ ʈʰ ɖ ɖʰ c cʰ cʼ k kʰ kʼ g ʔ
    s sː h
     d͡ʒ
    ɽ ɽː r rː
    l lː
    w wː w̃ w̃ː

    i iː ĩ ĩː u uː ũ ũː
    e eː ẽ ẽː ə əː ə̃ ə̃ː o oː õ õː
    ɛ ɛː ɛ̃ ɛ̃ː ɔ ɔː ɔ̃ ɔ̃ː
    a aː ã ãː

""")

check('sat-sat_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('sat-sat_FONIPA', GRAPHEMES, PHONEMES)
