# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[[:Sinh:] [:Cf:]]')

PHONEMES = makePhonemeSet("""
    p b t d c ɟ ʈ ɖ k g
    m n ɲ ŋ b̃ d̃ ɖ̃ ɟ̃ g̃ f s ʃ h
    r l j ʋ ɑ ɑ: æ æ: i i:
    u u: e e: o o: ə ə: ɑ:̃   æ:̃ ə:̃
    ɑi ɑu iu ei eu æi æu ɑi ɑu oi ou ui ɑ:i
    e:i o:i o:u u:i æ:i ɑ:u æ:u i:u w
    .

""")

check('si-si_FONIPA.txt', GRAPHEMES, PHONEMES)
regtest('si-si_FONIPA', GRAPHEMES, PHONEMES)
