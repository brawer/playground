# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, os, subprocess, unicodedata
import xml.etree.ElementTree as etree


PHOTOSHOP_PATH = 'typoterms-photoshop.tsv'
WINDOWS_PATH = 'typoterms-windows.tsv'
MACOS_PATH = '/System/Library/Frameworks/CoreText.framework/Resources'

SLANT_DEGREES = 12


def join(parts, lang):
    """(['Bold', 'Italic'], 'en') --> 'Bold Italic'

    Builds a synthetic face name by joining its parts.
    `lang` is a BCP47 language code, for example 'en' for English.
    """
    if lang in {'th', 'zh', 'zh_Hant'}:
        return ''.join(parts)
    return ' '.join(parts)


def read_macos_typoterms():
    styleNames = {}
    featureNames = {}
    styleNames[('opsz', '8', None)] = {'en': 'Caption'}
    styleNames[('opsz', '12', None)] = {'en': 'Text'}
    for dirname in os.listdir(MACOS_PATH):
        if not dirname.endswith('.lproj'):
            continue
        lang = dirname[:-6]
        lang = {'zh_CN': 'zh', 'zh_TW': 'zh_Hant'}.get(lang, lang)
        if lang == 'pl':
            continue
        snames = read_macos_plist(
            '%s/%s/StyleNames.strings' % (MACOS_PATH, dirname))
        for key, name in sorted(snames.items()):
            style = _MACOS_STYLES.get(key)
            if style:
                styleNames.setdefault(style, {})[lang] = name
        fnames = read_macos_plist(
            '%s/%s/FeatureSelectorNames.strings' % (MACOS_PATH, dirname))
        for key, name in sorted(fnames.items()):
            feature = _MACOS_FEATURES.get(key)
            if feature:
                featureNames.setdefault(feature, {})[lang] = name
    prune_variant_names(styleNames)
    prune_variant_names(featureNames)
    return {'styleNames': styleNames, 'featureNames': featureNames}


def prune_variant_names(names):
    alts = {}
    for (axis, value, alt) in names:
        if alt:
            alts.setdefault((axis, value), set()).add(alt)
    for (axis, value), alt in sorted(alts.items()):
        for a in alt:
            for lang, altName in sorted(list(names[(axis, value, a)].items())):
                name = names[(axis, value, None)].get(lang)
                if name == altName:
                    del names[(axis, value, a)][lang]


_MACOS_FEATURES = {
    'Capital Spacing': ('cpsp', None, None),
    'Optional Ligatures': ('dlig', None, None),
    'Small Capitals': ('smcp', None, None),
    'Small Caps': ('smcp', None, 'short'),
    'Slashed Zero': ('zero', None, None),
    'Tabular numbers': ('tnum', None, None),
    'Lining Numbers': ('lnum', None, None),
    'Old-Style Figures': ('onum', None, None),
    'Ordinals': ('ordn', None, None),
    'Proportional Numbers': ('pnum', None, None),
    'Diagonal Fractions': ('frac', None, None),
    'Vertical Fractions': ('afrc', None, None),
}


_MACOS_STYLES = {
    'backslanted': ('slnt', str(-SLANT_DEGREES), None),
    'upright': ('slnt', '0', None),
    'slanted': ('slnt', str(SLANT_DEGREES), None),
    'extraslant': ('slnt', str(2 * SLANT_DEGREES), None),

    'cursive': ('ital', '1', None),

    'titling': ('opsz', '18', None),
    'display': ('opsz', '72', None),
    'poster': ('opsz', '144', None),

    'ultra compressed': ('wdth', '50', 'variant'),
    'extra compressed': ('wdth', '62.5', 'variant'),
    'compressed': ('wdth', '75', 'variant'),
    'semi extended': ('wdth', '112.5', 'variant'),
    'extended': ('wdth', '125', 'variant'),
    'extra extended': ('wdth', '150', 'variant'),
    'ultra extended': ('wdth', '200', 'variant'),

    'extra narrow': ('wdth', '62.5', 'variant2'),
    'narrow': ('wdth', '75', 'variant2'),
    'wide': ('wdth', '125', 'variant2'),
    'extra wide': ('wdth', '150', 'variant2'),

    'ultra condensed': ('wdth', '50', None),
    'extra condensed': ('wdth', '62.5', None),
    'condensed': ('wdth', '75', None),
    'cond': ('wdth', '75', 'short'),
    'semi condensed': ('wdth', '87.5', None),
    'normal': ('wdth', '100', None),
    'semi expanded': ('wdth', '112.5', None),
    'expanded': ('wdth', '125', None),
    'extra expanded': ('wdth', '150', None),
    'ultra expanded': ('wdth', '200', None),

    'thin': ('wght', '100', None),
    'extra light': ('wght', '200', None),
    'ultra light': ('wght', '200', 'variant'),
    'light': ('wght', '300', None),
    'semi light': ('wght', '350', None),
    'demi light': ('wght', '350', 'variant'),
    'book': ('wght', '380', None),
    'regular': ('wght', '400', None),
    'medium': ('wght', '500', None),
    'semi bold': ('wght', '600', None),
    'demi bold': ('wght', '600', 'variant'),
    'bold': ('wght', '700', None),
    'extra bold': ('wght', '800', None), 
    'ultra bold': ('wght', '800', 'variant'), 
    'black': ('wght', '900', None),
    'heavy': ('wght', '900', 'variant'),
    'extrablack': ('wght', '950', None),
    'ultra heavy': ('wght', '950', 'variant'),
    'ultra black': ('wght', '950', 'variant2'),
}


def read_macos_plist(path):
    command = ['/usr/bin/plutil', '-convert', 'xml1', path, '-o', '-']
    doc = etree.fromstring(subprocess.check_output(command))
    keys = list(doc.findall('dict/key'))
    values = list(doc.findall('dict/string'))
    assert len(keys) == len(values), path
    names = {}
    for key, value in zip(keys, values):
        names[key.text.strip()] = value.text.strip()
    return names


def read_photoshop_typoterms():
    # https://www.microsoft.com/typography/otspec/dvaraxisreg.htm
    axis_tags = {
        'Italic': 'ital',
        'Optical size': 'opsz',
        'Slant': 'slnt',
        'Width': 'wdth',
        'Weight': 'wght',
    }
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        PHOTOSHOP_PATH)
    result = {tag: {'en': name} for name, tag in axis_tags.items()}
    for line in codecs.open(path, 'r', 'utf-8').readlines():
        line = line.strip()
        if not line or line[0] not in '0123456789':
            continue
        cols = line.split('\t')
        tag, name, lang = axis_tags[cols[1]], cols[4], cols[5]
        lang = 'zh_Hant' if lang == 'zh_TW' else lang.split('_')[0]
        name = unicodedata.normalize('NFC', name)
        result.setdefault(tag, {}).setdefault(lang, name)
    return {'axisNames': result}


_WINDOWS_STYLES = {
    ('WWS - Width', 'Ultra Condensed'): ('wdth', '50', None),
    ('WWS - Width', 'Extra Condensed'): ('wdth', '62.5', None),
    ('WWS - Width', 'Condensed'): ('wdth', '75', None),
    ('WWS - Width', 'Semi Condensed'): ('wdth', '87.5', None),
    ('WWS - Width', 'Normal'): ('wdth', '100', None),
    ('WWS - Width', 'Semi Expanded'): ('wdth', '112.5', None),
    ('WWS - Width', 'Expanded'): ('wdth', '125', None),
    ('WWS - Width', 'Extra Expanded'): ('wdth', '150', None),
    ('WWS - Width', 'Ultra Expanded'): ('wdth', '200', None),
    ('WWS - Width', 'Unknown'):  ('wdth', 'unknown', None),
    ('WWS - Width', 'Unspecified'):  ('wdth', 'unspecified', None),

    ('WWS - Weight', 'Unspecified'): ('wght', 'unspecified', None),
    ('WWS - Weight', 'Thin'): ('wght', '100', None),
    ('WWS - Weight', 'Extra Light'): ('wght', '200', None),
    ('WWS - Weight', 'Light'): ('wght', '300', None),
    ('WWS - Weight', 'Semi Light'): ('wght', '350', None),
    ('WWS - Weight', 'Regular'): ('wght', '400', None),
    ('WWS - Weight', 'Medium'): ('wght', '500', None),
    ('WWS - Weight', 'Semi Bold'): ('wght', '600', None),
    ('WWS - Weight', 'Bold'): ('wght', '700', None),
    ('WWS - Weight', 'Extra Bold'): ('wght', '800', None),
    ('WWS - Weight', 'Black'): ('wght', '900', None),
    ('WWS - Weight', 'Extra Black'): ('wght', '950', None),
    ('WWS - Weight', 'Unknown'): ('wght', 'unknown', None),

    ('WWS - Style', 'Normal'): ('ital', '0', None),
    ('WWS - Style', 'Italic'): ('ital', '1', None),
    ('WWS - Style', 'Unknown'): ('ital', 'unknown', None),

    ('WWS - Style', 'Oblique'): ('slnt', str(SLANT_DEGREES), None),
}


def read_windows_typoterms():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        WINDOWS_PATH)
    styleNames = {}
    combinedFaceNames = {}
    for line in codecs.open(path, 'r', 'utf-8').readlines():
        line = line.strip()
        if not line or line.startswith('Language\t'):
            continue
        cols = line.split('\t')
        lang = normalize_windows_language(cols[0])
        category, concept = cols[2], cols[3]
        name = unicodedata.normalize('NFC', cols[5]).strip()
        style = _WINDOWS_STYLES.get((category, concept))
        if style is not None:
            styleNames.setdefault(style, {})[lang] = name
        if (category, concept) == ('WWS - Style', 'Normal'):
            styleNames.setdefault(('slnt', '0', None), {})[lang] = name
        if (category, concept) == ('WWS - Style', 'Unknown'):
            styleNames.setdefault(('slnt', 'unknown', None), {})[lang] = name
        if category == 'WWS - combined facename':
            combinedFaceNames.setdefault(concept, {})[lang] = name
    return {'styleNames': styleNames, 'combinedFaceNames': combinedFaceNames}


def normalize_windows_language(lang):
    windows_languages = {
        'en-GB': 'en_GB',
        'es-MX': 'es_419',
        'fr-CA': 'fr_CA',
        'pt-PT': 'pt_PT',
        'sr-Latn-RS': 'sr_Latn',
        'zh-TW': 'zh_Hant',
    }
    l = windows_languages.get(lang)
    return l if l is not None else lang.split('-')[0]


def find_languages(terms):
    langs = set()
    for key in terms:
        for x in terms[key].values():
            langs.update(x.keys())
    return langs


def get_axis_names(terms, lang):
    result = {}
    for axisTag, names in terms.get('axisNames', {}).items():
        name = names.get(lang)
        if name is not None:
            result[axisTag] = name
    return result


def get_names(kind, terms, lang):
    baselang = lang.split('_')[0] if '_' in lang else None
    result = {}
    for key, names in terms.get(kind, {}).items():
        name = names.get(lang)
        basename = names.get(baselang) if baselang else None
        if name is not None and name != basename:
            result[key] = name
    return result


def xmlescape(s):
    return s.replace('&', '&amp;')


def get_style_sort_key(key):
    axisTag, axisValue, alt = key
    if axisValue and axisValue[0] in '0123456789':
        return (axisTag, float(axisValue), alt)
    else:
        return (axisTag, axisValue, alt)

        
def write_xml(terms, lang, out):
    baselang = lang.split('_')[0] if '_' in lang else None
    axisNames = get_axis_names(terms, lang)
    styleNames = get_names('styleNames', terms, lang)
    featureNames = get_names('featureNames', terms, lang)
    if not axisNames and not styleNames and not featureNames:
        print('**** SKIPPING', lang)
        return

    prefix = '\t'
    out.write(prefix + '<!-- in common/main/%s.xml -->\n' % lang)
    out.write(prefix + '<typographicNames>\n')
    for tag, name in sorted(axisNames.items()):
        out.write(prefix + '\t<axisName type="%s">%s</axisName>\n' %
                  (tag, xmlescape(name)))
    for key in sorted(featureNames.keys(), key=get_style_sort_key):
        name = featureNames[key]
        type, subtype, alt = key
        assert subtype is None
        out.write(prefix)
        out.write('\t<featureName type="%s"' % type)
        if alt:
            out.write(' alt="%s"' % xmlescape(alt))
        out.write('>%s</featureName>\n' % xmlescape(name))
    for styleKey in sorted(styleNames.keys(), key=get_style_sort_key):
        name = styleNames[styleKey]
        type, subtype, alt = styleKey
        out.write(prefix)
        out.write('\t<styleName type="%s" subtype="%s"' % (type, subtype))
        if alt:
            out.write(' alt="%s"' % xmlescape(alt))
        out.write('>%s</styleName>\n' % xmlescape(name))
    out.write(prefix + '</typographicNames>\n\n')


def get_name(names, lang):
    if lang in names:
        return names[lang]
    if '_' in lang:
        baselang = lang.split('_')[0]
        if baselang in names:
            return names[baselang]
    return names['en']


def synthesize_facename(terms, lang, var):
    styleNames = terms['styleNames']
    parts = []
    width = var.get('wdth', '100')
    if width != '100':
        widthKey = ('wdth', width, None)
        parts.append(get_name(styleNames[widthKey], lang))
    weight = var.get('wght', '400')
    if weight != '400':
        weightKey = ('wght', weight, None)
        parts.append(get_name(styleNames[weightKey], lang))
    italic = var.get('ital', '0')
    if italic != '0':
        italicKey = ('ital', italic, None)
        parts.append(get_name(styleNames[italicKey], lang))
    slant = var.get('slnt', '0')
    if slant != '0':
        slantKey = ('slnt', slant, None)
        parts.append(get_name(styleNames[slantKey], lang))
    if parts:
        return join(parts, lang)
    else:
        return styleNames[('wdth', 100, None)]


# Make sure that our heuristic for synthesizing face names gives the same
# results as in Microsoft's localization data.
def check_combined_facenames(terms, out):
    digits = '0123456789'
    names = get_names('styleNames', terms, 'en')
    weights = {name: value for (axis, value, alt), name in names.items()
               if axis == 'wght' and value[0] in digits}
    widths = {name: value for (axis, value, alt), name in names.items()
              if axis == 'wdth' and value[0] in digits}
    combined = {}
    for widthName, width in widths.items():
        for weightName, weight in weights.items():
            parts = []
            if widthName != 'Normal': parts.append(widthName)
            if weightName != 'Regular': parts.append(weightName)
            combinedName = join(parts, 'en')
            if combinedName:
                combined[combinedName] = {'wdth': width, 'wght': weight}
            combined[join(parts + ['Italic'], 'en')] = {
                'wdth': width,
                'wght': weight,
                'ital': '1'
            }
            combined[join(parts + ['Oblique'], 'en')] = {
                'wdth': width,
                'wght': weight,
                'slnt': str(SLANT_DEGREES)
            }
    out.write('Face\tLanguage\tCLDR\tWindows\n')
    for combinedKey, combinedNames in sorted(terms['combinedFaceNames'].items()):
        var = combined[combinedKey]
        for lang, windowsName in sorted(combinedNames.items()):
            synthName = synthesize_facename(terms, lang, var)
            out.write('\t'.join([combinedKey,lang, synthName, windowsName]))
            out.write('\n')


if __name__ == '__main__':
    terms = {}
    terms.update(read_macos_typoterms())
    terms.update(read_photoshop_typoterms())
    #terms.update(read_windows_typoterms())
    #with codecs.open('combined-facenames.tsv', 'w', 'utf-8') as out:
    #    check_combined_facenames(terms, out)
    with codecs.open('typoterms.xml', 'w', 'utf-8') as out:
        out.write('<terms>\n')
        for lang in sorted(find_languages(terms)):
            write_xml(terms, lang, out)
        out.write('</terms>\n')
