# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, collections, icu, os, re, unicodedata, urllib

# TODO: Change to googlei18n/language-resources after this pull request
# got merged: https://github.com/googlei18n/language-resources/pull/11
UPSTREAM_URL = ('https://raw.githubusercontent.com/brawer/'
                'language-resources/master/bn/')
CACHE_DIR = '/tmp/cache-lexicon-bn'
LOCALE = icu.Locale('bn')
COLLATOR = icu.Collator.createInstance(LOCALE)


def open_upstream_file(filename):
    cache = os.path.join(CACHE_DIR, filename.replace('/', '-'))
    if not os.path.exists(cache):
        content = urllib.urlopen(UPSTREAM_URL + filename).read()
        with open(cache, 'wb') as out:
            out.write(content)
    return open(cache, 'rb')


# http://universaldependencies.org/u/pos/
PARTS_OF_SPEECH = {
    'Adjective': 'ADJ',
    'Noun': 'NOUN',
    'Verb': 'VERB',
    'adjective': 'ADJ',
    'en': 'X',
    'english': 'X',
    'finite': 'VERB',
    'letter': 'PROPN',
    'letter-en': 'PROPN',
    'noun': 'NOUN',
    'participle': 'VERB',
    'past': 'VERB',
    'pronoun': 'PRON',
    'verb': 'VERB',
}


FEATURES = {
    # http://universaldependencies.org/u/feat/Tense.html
    # http://universaldependencies.org/u/feat/VerbForm.html
    'finite': 'VerbForm=Fin',
    'past': 'Tense=Past',
    'participle': 'VerbForm=Part',
}


def read_lexicon():
    lex = []
    with open_upstream_file('data/lexicon.tsv') as f:
        for line in f.read().decode('utf-8').splitlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            columns = line.split('\t')
            if len(columns) == 2:
                graph, phon = [col.strip() for col in columns]
                lex.append((graph, '*', '*', phon))
            elif len(columns) == 3:
                form, pron, annotation = [col.strip() for col in columns]
                form = unicodedata.normalize('NFC', form)
                pos = PARTS_OF_SPEECH[annotation]
                feat = FEATURES.get(annotation, '*')
                lex.append((form, pos, feat, pron))
            else:
                raise ValueError(line)
    return lex


def read_phonemes():
    phonemes = {'.': '.'}
    with open_upstream_file('phonemes.txt') as f:
        for line in f:
            ph, ipa = [c.strip() for c in line.decode('utf-8').split('\t')]
            phonemes[ph] = ipa
    return phonemes


def compare_entry(a, b):
    a = '\t'.join(a)
    b = '\t'.join(b)
    if COLLATOR.greater(a, b):
        return 1
    elif COLLATOR.greaterOrEqual(a, b):
        return 0
    else:
        return -1


def ipa(t, phonemes):
    return ''.join([phonemes[p] for p in t.split()])


if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    phonemes = read_phonemes()
    lex = [(word, pos, feat, ipa(s, phonemes)) for word, pos, feat, s in read_lexicon()]
    lex.sort(cmp=compare_entry)
    print('\t'.join(['Form', 'PartOfSpeech', 'Features', 'Pronunciation']))
    print()
    print('# SPDX-License-Identifier: Unicode-DFS-2016')
    print()
    for word, pos, feat, pron in lex:
        print('\t'.join([word, pos, feat, pron]).encode('utf-8'))
