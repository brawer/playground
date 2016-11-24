#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# Finds missing exemplar characters in Unicode CLDR by comparing to fontconfig.
# See http://unicode.org/cldr/trac/ticket/9497 for background.

from __future__ import unicode_literals
import codecs
import icu
import os
import re
import unicodedata
import xml.etree.ElementTree as etree
from xml.sax.saxutils import escape as xmlescape

# Run "svn co svn+ssh://unicode.org/repos/cldr/trunk" to download.
CLDR_SOURCE = '~/src/cldr2/trunk'

# Run "git clone git://anongit.freedesktop.org/fontconfig" to download.
FONTCONFIG_SOURCE = '~/src/fontconfig'

# Template for generating output files.
CLDR_EXEMPLAR_XML_START = \
"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE ldml SYSTEM "../../common/dtd/ldml.dtd">
<!-- Copyright © 2016 Unicode, Inc.
CLDR data files are interpreted according to the LDML specification (http://unicode.org/reports/tr35/)
For terms of use, see http://www.unicode.org/copyright.html
-->
<ldml>
	<identity>
		<version number="$Revision$"/>
		<language type="%(language)s"/>
		<script type="%(script)s"/>
	</identity>
	<layout>
		<orientation>
			<characterOrder>%(characterOrder)s</characterOrder>
			<lineOrder>%(lineOrder)s</lineOrder>
		</orientation>
	</layout>
	<characters>
		<exemplarCharacters%(references)s>%(characters)s</exemplarCharacters>
	</characters>
"""

CLDR_EXEMPLAR_XML_REFERENCE = \
'\t\t<reference type="%(type)s" uri="%(uri)s">%(text)s</reference>\n'


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


def extract_urls(s):
    s = s.replace(' www.', ' http://www.')  # "Source: www.eki.ee/letter"
    s = s.replace('www.everytype.com', 'www.evertype.com')  # typo in source
    return re.findall(r'http[s]?://[^\s]+', s)


# CLDR only has lowercase characters in its exemplars,
# and uses Unicode normalization form NFC.
def normalize_fontconfig_char(c):
    return unicodedata.normalize('NFC', c.lower())


def read_fontconfig_orth(path):
    """filepath to fontconfig *.orth file --> (icu.UnicodeSet, [references])"""
    result = icu.UnicodeSet()
    references = [
        'https://cgit.freedesktop.org/fontconfig/tree/fc-lang/' +
        os.path.basename(path)
    ]
    with codecs.open(path, 'r', 'utf-8') as f:
        for line in f:
            references.extend(extract_urls(line))
            line = line.split('#')[0].strip().split('\t')[0].strip()
            if not line:
                continue
            elif line.startswith('include '):
                incfile = os.path.join(os.path.dirname(path), line.split()[1])
                result.addAll(read_fontconfig_orth(incfile)[0])
            else:
                r = [int(x, 16) for x in line.split('-') if x.strip()]
                if len(r) == 1:
                    result.add(normalize_fontconfig_char(unichr(r[0])))
                elif len(r) == 2:
                    for c in range(r[0], r[1] + 1):
                        result.add(normalize_fontconfig_char(unichr(c)))
                else:
                    raise ValueError(path)
    result = result.compact()
    return (result, references)


def read_cldr_exemplars():
    result = {}
    for directory in ('seed', 'exemplars', 'common'):
        path = os.path.expanduser(os.path.join(CLDR_SOURCE, directory, 'main'))
        for filename in os.listdir(path):
            if filename.endswith('.xml'):
                lang, exemplars = read_cldr_file(os.path.join(path, filename))
                result[lang] = (exemplars, '%s/main/%s' % (directory, filename))
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
        if char.lower() in s:
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


def get_cldr_exemplars_by_type(lang, key, exemplars):
    subtags = lang.split('_')
    for i in range(len(subtags), 0, -1):
        result, source = exemplars.get('_'.join(subtags[:i]), (None, None))
        if result and key in result:
            return result[key], source
    return None, None


def get_cldr_exemplars(lang, exemplars):
    main, src = get_cldr_exemplars_by_type(lang, 'main', cldr_exemplars)
    if not main:
        return None, set()
    result = icu.UnicodeSet(main)
    sources = {src}
    aux, src = get_cldr_exemplars_by_type(lang, 'auxiliary', cldr_exemplars)
    if aux:
        result.addAll(aux)
        sources.add(src)
    index, src = get_cldr_exemplars_by_type(lang, 'index', cldr_exemplars)
    if index:
        result.addAll(index)
        sources.add(src)
    return result, sources


def get_reference_description(url):
    if url.startswith('http://www.eki.ee/'):
        return 'Institute of the Estonian Language'
    elif url.startswith('https://cgit.freedesktop.org/fontconfig/tree/'):
        return 'Fontconfig project'
    elif url.startswith('http://en.wikipedia.org/'):
        return 'Wikipedia'
    elif url.startswith('http://li.wikipedia.org/'):
        return 'Wikipedia'
    elif url.startswith('http://titus.uni-frankfurt.de/'):
        return 'University of Frankfurt: TITUS (Thesaurus Indogermanischer Text- und Sprachmaterialien), Unicode Sample Page Cyrillic Alphabets of Non-Slavic Languages'
    elif url.startswith('http://www.sil.org/iso639-3/'):
        return 'ISO 639-3 Registration Authority'
    elif url.startswith('http://www.omniglot.com/'):
        return 'Omniglot'
    elif url.startswith('http://www.evertype.com/alphabets/'):
        return 'Michael Everson: The Alphabets of Europe'
    return '[missing]'


def escape_for_unicodeset(char):
    if char in '[]{}\\':
        return '\\' + char
    else:
        return char

    
def format_unicodeset(uset):
    ranges = []
    for i in range(uset.getRangeCount()):
        if len(uset.getRangeStart(i)) != 1 or len(uset.getRangeEnd(i)) != 1:
            return uset.toPattern()
        start = ord(uset.getRangeStart(i))
        end = ord(uset.getRangeEnd(i))
        if end - start < 3:
            ranges.extend([escape_for_unicodeset(unichr(c))
                           for c in range(start, end + 1)])
        else:
            ranges.append('%s-%s' %
                          (escape_for_unicodeset(unichr(start)),
                           escape_for_unicodeset(unichr(end))))
    result = '[%s]' % ' '.join(ranges)
    # Make sure we don't change semantics with our pretty-pretting.
    if icu.UnicodeSet(result).toPattern() != uset.toPattern():
        return uset.toPattern()
    return result


def write_additions(deltas, out):
    for lang, (chars, refs, cldr_sources) in sorted(deltas.items()):
        locale = icu.Locale(lang)
        out.write('\n\n### %s: %s\n\n' % (lang, locale.getDisplayName()))
        reflist = ['R%d' % i for i in range(1, len(refs) + 1)]
        references = ' references="%s"' % ' '.join(reflist) if reflist else ''
        if locale.getScript() in ('Arab', 'Thaa', 'Nkoo', 'Syrc'):
            characterOrder = 'right-to-left'
        else:
            characterOrder = 'left-to-right'
        out.write('```xml\n')
        out.write(CLDR_EXEMPLAR_XML_START % {
            'language': locale.getLanguage(),
            'script': locale.getScript(),
            'characterOrder': characterOrder,
            'lineOrder': 'top-to-bottom',
            'characters': xmlescape(format_unicodeset(chars)),
            'references': xmlescape(references),
        })
        if refs:
            out.write('\t<references>\n')
            for i, ref in enumerate(refs):
                out.write(CLDR_EXEMPLAR_XML_REFERENCE % {
                    'type': reflist[i],
                    'uri': xmlescape(ref),
                    'text': xmlescape(get_reference_description(ref)),
                })
            out.write('\t</references>\n')
        out.write('</ldml>\n```\n\n')


def write_deltas(deltas, out):
    for lang, (chars, refs, cldr_sources) in sorted(deltas.items()):
        locale = icu.Locale(lang)
        out.write('\n\n### %s: %s\n\n' % (lang, locale.getDisplayName()))
        out.write('```\n%s\n```\n\n' % (format_unicodeset(chars)))
        if cldr_sources:
            markdown = '[%s](http://www.unicode.org/repos/cldr/trunk/%s)'
            s = [markdown % (src, src) for src in sorted(cldr_sources)]
            out.write('* CLDR: %s\n' % ' '.join(s))
        for ref in refs:
            out.write('* %s\n' % ref)


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
        cldrset, cldr_sources = get_cldr_exemplars(lang, cldr_exemplars)
        if cldrset:
            if cldrset.containsAll(fcset):
                ok[lang] = True
            else:
                mset = icu.UnicodeSet(fcset)
                mset.removeAll(cldrset)
                chars_missing[lang] = (mset, fcrefs, cldr_sources)
        elif likely.startswith(lang) or lang in DOUBLECHECKED_LANGTAGS:
            fully_missing[lang] = (fcset, fcrefs, cldr_sources)
        else:
            bogus[fclang] = (fcset, fcrefs, set())
    print('(a) Missing languages: %d languages' % len(fully_missing))
    print('(b) Missing characters: %d languages' % len(chars_missing))
    print('(c) Unsupported language codes: %d languages' % len(bogus))
    print('(d) OK: %d languages' % len(ok))

    out = codecs.open('missing_exemplars.md', 'w', 'utf-8')
    out.write(
        '# Exemplar characters missing from Unicode CLDR\n\n'
        'See [CLDR bug 9497](http://unicode.org/cldr/trac/ticket/9497)\n'
        'for background. This report has been automatically generated by a\n'
        '[Python script](https://github.com/brawer/playground/'
        'blob/master/cldr/find_missing_exemplars.py).\n\n')
    out.write(
        '1. [Missing languages](#missing-languages): %d\n'
        '2. [Languages with possibly missing characters]'
        '(#languages-with-possibly-missing-characters): %d\n'
        '3. [Unsupported language codes](#unsupported-language-codes): %d\n'
        '4. [Languages without problems](#languages-without-problems): %d\n\n' %
        (len(fully_missing), len(chars_missing), len(bogus), len(ok)))
    out.write(
        '\n\n'
        '## Missing languages\n\n'
        'For these %d languages, CLDR has no exemplar data at all.\n'
        'To match the conventions of the existing [exemplars data]'
        '(http://www.unicode.org/repos/cldr/trunk/exemplars/main)\n'
        'in CLDR, the language codes always contain a script subtag.\n'
        '\n'
        '**Proposal:** Add the following files to Unicode CLDR\n'
        'in directory `exemplars/main`.\n'
        '\n' %
        len(fully_missing))
    write_additions(fully_missing, out)
    out.write(
        '\n\n'
        '## Languages with possibly missing characters\n\n'
        'For these %d languages, CLDR already has exemplar data. However,\n'
        'fontconfig specifies additional characters beyond CLDR.\n'
        '\n'
        '**Proposal:** Manually go through each case and decide whether\n'
        'the CLDR data needs to be adjusted. Add reference URLs to the CLDR\n'
        'data files.\n\n' %
        len(chars_missing))
    write_deltas(chars_missing, out)
    out.write(
        '\n\n'
        '## Unsupported language codes\n\n'
        'For these %d languages, fontconfig uses a language code\n'
        'that could not be mapped to a Unicode language code. While\n'
        'the IANA language subtag registry for IETF BCP-47 contains\n'
        'entries for these codes, they indicate *language collections*\n'
        'which are not supported by Unicode CLDR.\n'
        '\n'
        '**Proposal:** Decide whether these exemplar sets make sense\n'
        'for any specific Berber or Sorbian languages. If so, manually adjust\n'
        'the CLDR data for those languages.\n\n' %
        len(bogus))
    write_deltas(bogus, out)
    out.write(
        '\n\n'
        '## Languages without problems\n\n'
        'For these %d languages, the exemplar characters of fontconfig\n'
        'are also present in CLDR. No action needed.\n\n' %
        len(ok))
    for lang in sorted(ok):
        out.write('* `%s` %s\n' % (lang, icu.Locale(lang).getDisplayName()))
