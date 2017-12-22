# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, os, unicodedata

PHOTOSHOP_PATH = 'typoterms-photoshop.tsv'
WINDOWS_PATH = 'typoterms-windows.tsv'


def join(parts, lang):
    """(['Bold', 'Italic'], 'en') --> 'Bold Italic'

    Builds a synthetic face name by joining its parts.
    `lang` is a BCP47 language code, for example 'en' for English.
    """
    if lang in {'th', 'zh', 'zh_Hant'}:
        return ''.join(parts)
    return ' '.join(parts)


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
    ('WWS - Weight', 'Regular'): ('wght', '400', None),
    ('WWS - Weight', 'Medium'): ('wght', '500', None),
    ('WWS - Weight', 'Semi Bold'): ('wght', '600', None),
    ('WWS - Weight', 'Bold'): ('wght', '700', None),
    ('WWS - Weight', 'Extra Bold'): ('wght', '800', None),
    ('WWS - Weight', 'Black'): ('wght', '900', None),
    ('WWS - Weight', 'Extra Black'): ('wght', '950', None),
    ('WWS - Weight', 'Semi Light'): ('wght', '350', None),
    ('WWS - Weight', 'Unknown'): ('wght', 'unknown', None),

    ('WWS - Style', 'Normal'): ('ital', '0', None),
    ('WWS - Style', 'Italic'): ('ital', '1', None),
    ('WWS - Style', 'Unknown'): ('ital', 'unknown', None),

    ('WWS - Style', 'Oblique'): ('slnt', '12', None),
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


def get_style_names(terms, lang):
    baselang = lang.split('_')[0] if '_' in lang else None
    result = {}
    for styleKey, names in terms.get('styleNames', {}).items():
        name = names.get(lang)
        basename = names.get(baselang) if baselang else None
        if name is not None and name != basename:
            result[styleKey] = name
    return result


def xmlescape(s):
    return s.replace('&', '&amp;')


def get_style_sort_key(key):
    axisTag, axisValue, alt = key
    if axisValue[0] in '0123456789':
        return (axisTag, float(axisValue), alt)
    else:
        return (axisTag, axisValue, alt)

        
def write_xml(terms, lang, out):
    baselang = lang.split('_')[0] if '_' in lang else None
    axisNames = get_axis_names(terms, lang)
    styleNames = get_style_names(terms, lang)
    if not axisNames and not styleNames:
        print('**** SKIPPING', lang)
        return

    prefix = '\t'
    out.write(prefix + '<!-- in common/main/%s.xml -->\n' % lang)
    out.write(prefix + '<typographicNames>\n')
    for tag, name in sorted(axisNames.items()):
        out.write(prefix + '\t<axisName type="%s">%s</axisName>\n' %
                  (tag, xmlescape(name)))
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
    names = get_style_names(terms, 'en')
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
            combined[join(parts + ['Italic'], 'en')] = {'wdth': width, 'wght': weight, 'ital': '1'}
            combined[join(parts + ['Oblique'], 'en')] = {'wdth': width, 'wght': weight, 'slnt': '12'}
    out.write('Face\tLanguage\tCLDR\tWindows\n')
    for combinedKey, combinedNames in sorted(terms['combinedFaceNames'].items()):
        var = combined[combinedKey]
        for lang, windowsName in sorted(combinedNames.items()):
            synthName = synthesize_facename(terms, lang, var)
            out.write('\t'.join([combinedKey,lang, synthName, windowsName]))
            out.write('\n')


if __name__ == '__main__':
    terms = read_windows_typoterms()
    terms.update(read_photoshop_typoterms())
    with codecs.open('combined-facenames.tsv', 'w', 'utf-8') as out:
        check_combined_facenames(terms, out)
    with codecs.open('typoterms.xml', 'w', 'utf-8') as out:
        out.write('<terms>\n')
        for lang in sorted(find_languages(terms)):
            write_xml(terms, lang, out)
        out.write('</terms>\n')
