# coding: utf-8

from __future__ import unicode_literals
import argparse, codecs, collections, re, unicodedata

IPA = {
    '@': 'ə',
    'GG': 'ɡʰ',
    'KK': 'kʰ',
    'NG': 'ŋ',
    'NJ': 'ɲ',
    'SS': 'ʃ',
    'a': 'a',
    'aj': 'aj',
    'aw': 'aw',
    'b': 'b',
    'd': 'd',
    'dZ': 'd͡ʒ',
    'e': 'e',
    'f': 'f',
    'g': 'ɡ',
    'h': 'h',
    'i': 'i',
    'j': 'j',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'o': 'o',
    'oj': 'oj',
    'p': 'p',
    'r': 'r',
    's': 's',
    't': 't',
    'tS': 't͡ʃ',
    'u': 'u',
    'v': 'v',
    'w': 'w',
    'x': 'x',
    'z': 'z',
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()
    result = []
    for line in codecs.open(args.input, 'r', encoding='utf-8'):
        word, phones = line.split('\t')
        if word in {'<sil>', '<UNK>'}:
            continue
        ipa = ''.join([IPA[p] for p in phones.split()])
        result.append((word.strip(), ipa))
    for word, ipa in sorted(result):
        print('\t'.join([word, ipa]))
