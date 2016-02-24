# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import icu

class HindiUrduTransform(object):
    def __init__(self):
        with open('Devanagari-InterIndic.txt') as rules:
            self.fromHindi = icu.Transliterator.createFromRules(
                'Hindi-InterIndic', rules.read(),
                icu.UTransDirection.FORWARD)
        with open('InterIndic-Urdu.txt') as rules:
            self.toUrdu = icu.Transliterator.createFromRules(
                'InterIndic-Urdu', rules.read(),
                icu.UTransDirection.FORWARD)

    def transliterate(self, s):
        interindic = self.fromHindi.transliterate(s)
        return self.toUrdu.transliterate(interindic)


if __name__ == '__main__':
    with codecs.open('udhr_hi.txt', 'r', 'utf-8') as input_file:
        text = input_file.read()
    t = HindiUrduTransform()
    print t.transliterate(text).encode('utf-8')

