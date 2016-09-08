# -*- coding: utf-8 -*-

# Hacky script that modernizes the Zycon font from 1993.
# Removes unused glyphs, fixes names, installs 'cmap' for Unicode Emoji.


import argparse
import tempfile
from fontTools import subset
from fontTools import ttLib
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable


GLYPHS = {
    'exclam': 'uni2600',
    'quotedbl': 'u1F55B',
    'numbersign': 'u1F6B4',
    'dollar': 'u1F98E',
    'percent': 'u1F989',
    'quotesingle': 'u1F3F5',
    'parenleft': 'u1F512',
    'parenright': 'u0231A',
    'asterisk': 'u1F590',
    'plus': 'u1F415',
    'comma': 'u1F422',
    'hyphen': 'u1F408',
    'slash': 'uni272F',
    'zero': 'u1F31D',
    'one': 'uni2B24',
    'two': 'uni279F',
    'three': 'u1F4A1',
}

def setName(font, nameID, name, encoding=1):
    font['name'].setName(name, nameID=nameID,
                         platformID=3, platEncID=encoding, langID=0x409)


def makeSampleText():
    result = []
    for v in GLYPHS.values():
        if v.startswith('uni'):
            c = int(v[3:], 16)
            result.append(unichr(c))
        elif v.startswith('u1'):
            result.append(eval("u'\U000" + v[1:] + "'"))
    return u''.join(sorted(result))


def modernizeZycon(fontPath, newFontPath):
    origFont = ttLib.TTFont(fontPath)
    if origFont['name'].getDebugName(1) != u'\x00Zycon':  # name was broken
        raise ValueError('%s is not the old Zycon font' % fontPath)

    # Reduce the file size by subsetting to the glyphs that are actually used.
    subsetpath = tempfile.mktemp(suffix='.ttf')
    ttxpath = tempfile.mktemp(suffix='.ttx')
    subset.main([fontPath, '--notdef-glyph', '--notdef-outline',
                '--glyphs=space,' + ','.join(sorted(GLYPHS.keys())),
                '--output-file=%s' % subsetpath])
    font = ttLib.TTFont(subsetpath)

    # Replace the name table.
    # TODO: Negotiate licensing terms between Font Bureau and Unicode,
    # so this font can be included into the upcoming OpenType test suite.
    font['name'].names = []
    setName(font, 0,
            u'Copyright ©1993–2016 by The Font Bureau, Inc. ' +
            u' with Reserved Font Name “Zycon”')
    setName(font, 1, 'Zycon')
    setName(font, 2, 'Regular')
    setName(font, 5, 'Version 1.8')
    setName(font, 6, 'Zycon-Regular')
    setName(font, 9, 'David Berlow')
    setName(font, 14, 'https://opensource.org/licenses/OFL-1.1')
    setName(font, 19, makeSampleText(), encoding=10)
    del font['hdmx']

    # Isn’t there a better way to rename glyphs with fontTools?
    font.saveXML(ttxpath)
    with open(ttxpath, 'r') as ttxFile:
        ttx = ttxFile.read()
    for old, new in GLYPHS.items():
        ttx = ttx.replace('"%s"' % old, '"%s"' % new)
    with open(ttxpath, 'w') as out:
        out.write(ttx)
    font = ttLib.TTFont()
    font.importXML(ttxpath)

    cmap4 = CmapSubtable.newSubtable(4)
    cmap4.platformID, cmap4.platEncID, cmap4.language = 3, 1, 0
    cmap4.cmap = {0x20: 'space'}
    cmap12 = CmapSubtable.newSubtable(12)
    cmap12.platformID, cmap12.platEncID, cmap12.language = 3, 10, 0
    cmap12.cmap = {0x20: 'space'}
    for glyph in GLYPHS.values():
        if glyph.startswith('uni'):
            cmap4.cmap[int(glyph[3:], 16)] = glyph
            cmap12.cmap[int(glyph[3:], 16)] = glyph
        elif glyph.startswith('u'):
            cmap12.cmap[int(glyph[1:], 16)] = glyph
    font['cmap'].tables = [cmap4, cmap12]
    empty = font['glyf']['.notdef']
    emptyMetrics = font['hmtx']['.notdef']
    font['glyf']['.notdef'] = font['glyf']['space']
    font['hmtx']['.notdef'] = font['hmtx']['space']
    font['glyf']['space'] = empty
    font['hmtx']['space'] = [880, 0]
    font.save(newFontPath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modernize the Zycon font.')
    parser.add_argument(
        '--font', default='path/to/ZyconRegular.ttf',
        help='path to original Zycon.ttf')
    parser.add_argument(
        '--out', default='path/to/Zycon-Regular.ttf',
        help='path where the modernized font will be written')
    args = parser.parse_args()
    modernizeZycon(args.font, args.out)
