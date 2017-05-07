# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

from cldr_util import makePhonemeSet, match, check, regtest

GRAPHEMES = icu.UnicodeSet()
GRAPHEMES.applyPattern('[:Mymr:]')

# TODO: Differences to JIPA, which we should resolve:
# - in JIPA, /ɴ/ is not in the phoneme list
# - in JIPA, /t͡ɕ/, /t͡ɕʰ/, and /d͡ʑ/ are /t͡ʃ/, /t͡ʃʰ/, and /d͡ʒ/
# - in JIPA, /ð/ is a phoneme (but none of our rules produce it)
# - in JIPA, /ɹ/ is a phoneme (but none of our rules produce it);
#   apparently it is used for loanwords of Pali origin.
#   Wikipedia says it's also used for English loanwords.
# - in JIPA, /w̥/ is /ʍ/
# - in JIPA, these are the vowels: /i/ /u/ /e/ /o/ /ə/ /ɛ/ /ɔ/ /a/
# - in JIPA, there are four tones: low /ma/, high /má/, creaky /ma̰/
#   and killed /maʔ/. In our rules, we currently have also /à/.
# - in JIPA, there are much fewer diphthongs. Are ours really phonemic?
#
# TODO: Can/should we emit syllable markers? /./

PHONEMES = makePhonemeSet("""

    m̥ m n̥ n ɲ̥ ɲ ŋ̊  ŋ ɴ
    p pʰ b t tʰ d t͡ɕ t͡ɕʰ d͡ʑ k kʰ g ʔ
    θ s sʰ z ʃ h
    w̥ w j
    l̥ l

    í ì ḭ
    ú ù ṵ
    ʊ ʊ́ ʊ̀ ʊ̰
    ɪ ɪ́ ɪ̀ ɪ̰
    e é è ḛ
    ó ò o̰
    ə
    ɛ ɛ́ ɛ̀ ɛ̰
    ɔ́ ɔ̀ ɔ̰
    æ
    a á à a̰

    eɪ̯ éɪ̯ èɪ̯ ḛɪ̯
    oʊ̯ óʊ̯ òʊ̯ o̰ʊ̯
    əʊ̯
    aɪ̯ áɪ̯ àɪ̯ a̰ɪ̯
    aʊ̯ áʊ̯ àʊ̯ a̰ʊ̯

    .

""")


check('my-fonipa-t-my', GRAPHEMES, PHONEMES)
regtest('my-fonipa-t-my', GRAPHEMES, PHONEMES)
