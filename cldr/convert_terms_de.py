# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import codecs
import re
from xml.sax.saxutils import escape as xmlescape

HEADER = """<ldml>
	<identity>
		<version number="$Revision$"/>
		<language type="%s"/>
	</identity>
​	<terms>
"""

FOOTER = """	</terms>\n</ldml>\n"""

TERM = """		<term>
			<t>%s</t>
			<hyph>%s</hyph>
		</term>
"""

def MakeStream(lang):
    s = codecs.open('terms-%s.xml' % lang, 'w', 'utf-8')
    s.write(HEADER % xmlescape(lang))
    return s

RE_BAD_HYPHEN = re.compile(r'([•]+)[◦]+')
RE_BLACK_DOTS = re.compile(r'([•]+)')

def ConvertHyph(w):
    w = w.replace('-', '•').replace('.', '◦')
    w = w.replace('===', '•••••')
    w = w.replace('==', '••••')
    w = w.replace('=', '•••').replace('<=', '•••').replace('=>', '•••')
    w = w.replace('<', '••').replace('>', '••')
    w = w.replace('/', '|')
    num_dots = sorted(
        list(set([1] + [len(x) for x in RE_BLACK_DOTS.findall(w)])))
    mapping = dict([(num_dots, '•' * (order+1))
                    for order, num_dots in enumerate(num_dots)])
    w = RE_BLACK_DOTS.sub(lambda s:mapping[len(s.group(1))], w)
    w = RE_BAD_HYPHEN.sub(lambda s:'◦' * len(s.group(1)), w)
    if '[' in w:
        #print(w.encode('utf-8'))
        assert w.count('[') == 1
        assert w.count(']') == 1
        assert w.count('|') <= 2
        prefix, rest = w.split('[', 1)
        infix1, rest = rest.split('|', 1)
        infix2, suffix = rest.split(']', 1)
        return [prefix + infix1 + suffix, prefix + infix2 + suffix]
    return [w]

RE_COMPLEX_HYPHEN = re.compile(r'{[^}]*}')

def MakeTerm(hyph):
    term = hyph.replace('•', '').replace('◦', '')
    return RE_COMPLEX_HYPHEN.sub(lambda s:s.group(0).split('|')[0][1:], term)

def Convert():
    de = MakeStream('de')
    de_CH = MakeStream('de-CH')
    de_1901 = MakeStream('de-1901')
    de_CH_1901 = MakeStream('de-CH-1901')
    for line in codecs.open('/home/sascha/src/wortliste/wortliste', 'r',
                            'utf-8'):
        line = line.split('#')[0].strip()
        cols = (line.split(';') + [None] * 8)[:8]
        hyph = cols[1]
        hyph_de = hyph_de_CH = hyph_de_1901 = hyph_de_CH_1901 = []
        if hyph and hyph != '-2-':
            hyph_de = hyph_de_CH = hyph_de_1901 = hyph_de_CH_1901 = \
                      ConvertHyph(hyph)
        else:
            if cols[2] and cols[2] != '-3-':
                hyph_de_1901 = ConvertHyph(cols[2])
            if cols[3] and cols[3] != '-4-':
                hyph_de = ConvertHyph(cols[3])
            if cols[4] and cols[4] != '-5-':
                hyph_de_CH = hyph_de_CH_1901 = ConvertHyph(cols[4])
            else:
                hyph_de_CH = hyph_de
                hyph_de_CH_1901 = hyph_de_1901
            if cols[5] and cols[5] != '-6-':
                hyph_de_CH_1901 = ConvertHyph(cols[5])
            if cols[6] and cols[6] != '-7-':
                hyph_de_CH = ConvertHyph(cols[6])
            if cols[7] and cols[7] != '-8-':
                hyph_de_CH_1901 = ConvertHyph(cols[7])
        for h in hyph_de:
            de.write(TERM % (xmlescape(MakeTerm(h)), xmlescape(h)))
        for h in hyph_de_CH:
            if 'ß' not in h:
                de_CH.write(TERM % (xmlescape(MakeTerm(h)), xmlescape(h)))
        for h in hyph_de_1901:
            de_1901.write(TERM % (xmlescape(MakeTerm(h)), xmlescape(h)))
        for h in hyph_de_CH_1901:
            if 'ß' not in h:
                de_CH_1901.write(TERM % (xmlescape(MakeTerm(h)), xmlescape(h)))

    for s in (de, de_CH, de_1901, de_CH_1901):
        s.write(FOOTER)
        s.close()

if __name__ == '__main__':
    Convert()
    #print MakeTerm('Blut•zu{ck|k◦k}er•spie◦gel')
    #<hyph loc="de-1901">Blut•zu{ck/k◦k}er•spie◦gel</hyph>
    
