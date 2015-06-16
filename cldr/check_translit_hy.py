# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

rules = codecs.open('hy-hy_FONIPA.txt', 'r', 'utf-8').read()
translit = icu.Transliterator.createFromRules(
    "hy-hy_FONIPA", rules, icu.UTransDirection.FORWARD)

words = {}
udhr = codecs.open('udhr-hy.txt', 'r', 'utf-8').read()
for c in '֊-։«,:;.0123456789()': udhr = udhr.replace(c, ' ')




for word in udhr.split():
    words[word] = words.get(word, 0) + 1
for count, word in reversed(sorted([(v,k) for k,v in words.items()])):
    t = translit.transliterate(word)
    print ('%s\t%s' % (word, t)).encode('utf-8')


