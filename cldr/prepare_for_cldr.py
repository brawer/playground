# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import codecs
import sys
import unicodedata

CLDR_PATH = "/home/sascha/src/cldr"

HEADER = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE supplementalData SYSTEM "../../common/dtd/ldmlSupplemental.dtd">
<!-- Copyright © 1991-2015 Unicode, Inc.
	CLDR data files are interpreted according to the LDML specification (http://unicode.org/reports/tr35/) 
	For terms of use, see http://www.unicode.org/copyright.html -->
<supplementalData>
	<version number="$Revision$" />
	<transforms>
		<transform source="%s" target="%s" direction="forward" draft="contributed">
"""


FOOTER = """		</transform>
	</transforms>
</supplementalData>
"""


def PrepareForCLDR(lang):
    target = "%s_FONIPA" % lang
    path = "%s-%s.txt" % (lang, target)
    out = codecs.open(CLDR_PATH + "/common/transforms/%s-%s.xml" %
                      (lang, target), "w", "utf-8")
    out.write(HEADER % (lang, target))
    for line in codecs.open(path, "r", "utf-8"):
        line = unicodedata.normalize("NFC", line).strip()
        if not line or line[0] != '#':
            out.write(u"\t\t\t<tRule>%s</tRule>\n" % line)
        else:
            out.write(u"\t\t\t<comment>%s</comment>\n" % line)
    out.write(FOOTER)
    out.close()

    with codecs.open("test-%s-%s.txt" % (lang, target), "r", "utf-8") as test_in:
        with codecs.open(
            CLDR_PATH + "/tools/cldr-unittest/src/" +
            "org/unicode/cldr/unittest/data/transformtest/%s-%s.txt" %
            (lang, target), "w", "utf-8") as test_out:
            test_out.write(unicodedata.normalize("NFC", test_in.read()))


PrepareForCLDR('am')
