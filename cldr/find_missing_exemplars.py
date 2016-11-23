#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# Finds missing exemplar characters in Unicode CLDR by comparing to fontconfig.
# See http://unicode.org/cldr/trac/ticket/9497 for background.

from __future__ import unicode_literals
import codecs
import icu
import os
import re
import xml.etree.ElementTree as etree

# Run "svn co svn+ssh://unicode.org/repos/cldr/trunk" to download.
CLDR_SOURCE = '~/src/cldr2/trunk'

# Run "git clone git://anongit.freedesktop.org/fontconfig" to download.
FONTCONFIG_SOURCE = '~/src/fontconfig'


def read_likely_subtags():
    filepath = os.path.expanduser(
        os.path.join(CLDR_SOURCE, 'common/supplemental/likelySubtags.xml'))
    ldml = etree.parse(filepath).getroot()
    return {t.attrib['from']: t.attrib['to']
            for t in ldml.iterfind('./likelySubtags/likelySubtag')}


def read_language_aliases():
    filepath = os.path.expanduser(
        os.path.join(CLDR_SOURCE,
                     'common/supplemental/supplementalMetadata.xml'))
    ldml = etree.parse(filepath).getroot()
    return {t.attrib['type']: t.attrib['replacement']
            for t in ldml.iterfind('./metadata/alias/languageAlias')}


def read_fontconfig_exemplars():
    """Returns exemplar chars according to fontconfig."""
    result = {}
    path = os.path.expanduser(os.path.join(FONTCONFIG_SOURCE, 'fc-lang'))
    for filename in os.listdir(path):
        if not filename.endswith('.orth'):
            continue
        locale = icu.Locale.createFromName(filename[:-len('.orth')])
        chars = read_fontconfig_orth(os.path.join(path, filename))
        result[locale.getName()] = chars
    return result


def read_fontconfig_orth(path):
    """filepath to fontconfig *.orth file --> (icu.UnicodeSet, [references])"""
    result = icu.UnicodeSet()
    references = [
        'https://cgit.freedesktop.org/fontconfig/tree/fc-lang/' +
        os.path.basename(path)
    ]
    with codecs.open(path, 'r', 'utf-8') as f:
        for line in f:
            references.extend(re.findall(r'http[s]?://[^\s]+', line))
            line = line.split('#')[0].strip().split('\t')[0].strip()
            if not line:
                continue
            elif line.startswith('include '):
                incfile = os.path.join(os.path.dirname(path), line.split()[1])
                result.addAll(read_fontconfig_orth(incfile)[0])
            else:
                r = [int(x, 16) for x in line.split('-') if x.strip()]
                if len(r) == 1:
                    result.add(unichr(r[0]))
                elif len(r) == 2:
                    for c in range(r[0], r[1] + 1):
                        result.add(unichr(c) )
                else:
                    raise ValueError(path)
    result = result.compact()
    return (result, references)


def read_cldr_exemplars():
    result = {}
    path = os.path.expanduser(os.path.join(CLDR_SOURCE, 'exemplars/main'))
    for filename in os.listdir(path):
        if filename.endswith('.xml'):
            lang, exemplars = read_cldr_file(os.path.join(path, filename))
            result[lang] = exemplars
    path = os.path.expanduser(os.path.join(CLDR_SOURCE, 'common/main'))
    for filename in os.listdir(path):
        if filename.endswith('.xml'):
            lang, exemplars = read_cldr_file(os.path.join(path, filename))
            result[lang] = exemplars
    return result


def guess_script(s):
    scripts = {
        'A': 'Latn',
        'А': 'Cyrl',
        'я': 'Cyrl',
        'ء': 'Arab',
        'و': 'Arab',
        'अ': 'Deva',
        'প': 'Beng',
        'ሀ': 'Ethi',
        'ᐁ': 'Cans',
        'ⴱ': 'Tfng',
        'ᠠ': 'Mong',
        'ހ': 'Thaa',
        '߀': 'Nkoo',
        'ܐ': 'Syrc',
    }
    for char, script in scripts.items():
        if char in s:
            return script


def read_cldr_file(filepath):
    assert filepath.endswith('.xml'), filepath
    exemplars = {}
    ldml = etree.parse(filepath).getroot()
    lang = ldml.find('./identity/language').attrib['type']
    script = ldml.find('./identity/script')
    if script is not None:
        lang = lang + '_' + script.attrib['type']
    territory = ldml.find('./identity/territory')
    if territory is not None:
        lang = lang + '_' + territory.attrib['type']
    variants = sorted([t.attrib['type']
                       for t in ldml.iterfind('./identity/variant')])
    if variants is not None:
        lang = '_'.join([lang] + variants)
    tags = set(t.tag for t in ldml.iterfind('./identity/*'))
    if not tags.issubset({
            'version', 'language', 'script', 'territory', 'variant'}):
        raise ValueError('unexpected identity elements in %s' % filepath)
    for ex in ldml.iterfind('./characters/exemplarCharacters'):
        extype = ex.attrib.get('type', 'main')
        exemplars[extype] = icu.UnicodeSet(''.join(ex.itertext()))
    return lang, exemplars


# Whitelist of language tags that we accept as valid, even if CLDR
# has no likely subtags yet for the language subtag.
DOUBLECHECKED_LANGTAGS = {
    'an_Latn',   # Aragonese
    'crh_Latn',  # Crimean Tatar
    'doi_Deva',  # Dogri
    'ie_Latn',   # Interlingue
    'ik_Cyrl',   # Inupiaq
    'io_Latn',   # Igbo
    'ku_Cyrl',   # Kurdish
    'ku_Latn',   # Kurdish
    'kwm_Latn',  # Kwambi
    'pap_Latn',  # Papiamento
    'ps_Arab',   # Pashto
    'sat_Deva',  # Santali
    'sel_Cyrl',  # Selkup
    'shs_Latn',  # Shuswap
    'sid_Ethi',  # Sidamo
}


def get_cldr_exemplars(lang, key, exemplars):
    subtags = lang.split('_')
    for i in range(len(subtags), 0, -1):
        result = exemplars.get('_'.join(subtags[:i]))
        if result and key in result:
            return result[key]
    return None


if __name__ == '__main__':
    empty_uset = icu.UnicodeSet()
    chars_missing, fully_missing, ok, bogus = {}, {}, {}, {}
    likely_subtags = read_likely_subtags()
    language_aliases = read_language_aliases()
    cldr_exemplars = read_cldr_exemplars()
    fontconfig_exemplars = read_fontconfig_exemplars()
    for fclang, (fcset, fcrefs) in sorted(fontconfig_exemplars.items()):
        lang = language_aliases.get(fclang, fclang)
        if lang == 'ps_PK': lang = 'ps'
        if lang == 'pap_AN': lang = 'pap_Latn'
        if lang in {'pap_AW'}: continue
        likely = likely_subtags.get(lang, 'und')
        if lang not in cldr_exemplars and not lang.startswith('zh_'):
            pattern = fcset.toPattern()
            lang = '_'.join((lang.split('_')[0], guess_script(pattern)))
        cldrset = get_cldr_exemplars(lang, 'main', cldr_exemplars)
        if cldrset:
            if cldrset.containsAll(fcset):
                ok[lang] = True
            else:
                chars_missing[lang] = True
                pass #print lang, cldrset.toPattern(), fcset.toPattern()
        elif likely.startswith(lang) or lang in DOUBLECHECKED_LANGTAGS:
            fully_missing[lang] = (fcset, fcrefs)
        else:
            bogus[fclang] = (fcset, fcrefs)
    print('(a) Already in CLDR, no changes: %d languages' % len(ok))
    print('(b) Entirely missing from CLDR: %d languages' % len(fully_missing))
    print('(c) Some characters missing from CLDR: %d languages' %
          len(chars_missing))
    print('(d) Manual resolution needed: %d languages' % len(bogus))
    if True:
        print('')
        print('')
        print('(a) Already in CLDR, no changes: %d languages' % len(ok))
        print(' '.join(sorted(ok.keys())))
        print('')
        print('(b) Entirely missing from CLDR: %d languages' %
              len(fully_missing))
        for lang, (chars, refs) in sorted(fully_missing.items()):
            print('\t'.join(
                [lang, chars.toPattern(), '|'.join(refs)]).encode('utf-8'))
        print('')
        print('(c) Some characters missing from CLDR: %d languages' %
              len(chars_missing))
        print('')
        print('(d) Manual resolution needed: %d languages' % len(bogus))
