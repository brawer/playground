#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs, os, urllib


"""Removes diacritics from a Persian corpus. Output is tab-separated UTF-8."""

DIACRITICS = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653'


def unaccent(word):
    for c in DIACRITICS:
        word = word.replace(c, '')
    return word


def load_corpus():
    path = '/tmp/updt-with-diacritics.txt'
    if not os.path.exists(path):
        url = ('https://github.com/googlei18n/language-resources/raw/master/'
               'third_party/fa/updt/updt-with-diacritics.txt')
        with open(path, 'w') as out:
            out.write(urllib.urlopen(url).read())
    return path


def unaccent_corpus(path):
    for line in codecs.open(path, 'r', 'utf-8'):
        for c in ' ؛.,!?[+/];»:»()“‘" ؟؉؊؍،–—': line = line.replace(c, ' ')
        words = line.split()
        for word in words:
            # Remove word-final diacritcs
            last_char = word[-1]
            if last_char in DIACRITICS:
                word = word[:-1]
            print u'\t'.join([unaccent(word), word]).encode('utf-8')


if __name__ == '__main__':
    unaccent_corpus(load_corpus())
