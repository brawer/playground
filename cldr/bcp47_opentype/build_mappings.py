# -*- coding: utf-8 -*-

import md5, os, re, tempfile, urllib

# TODO: What to do with bcp47 extlang?
# TODO: Verify that all Syriac languages are included, seems to be goofy

# TODO: What to do with sr Serbian? Tricky because script.

# TODO: Register a macrolang for "Comorian"?
# https://en.wikipedia.org/wiki/Comorian_language
# OpenType groups swb, wlc, wni, zdj into a single OpenType CMR

SPECIAL = {
    '*-fonnapa': 'APPH',
    '*-fonipa': 'IPPH',
    '*-Geok': 'KGE ', # Khutsuri Georgian
    '*-Latg': 'IRT ', # Irish Traditional
    'mnk': 'MND ',  # OpenType lists MND, MNK
    'scs': 'SCS ',  # OpenType lists ATH, SCS, SLA
    'kca': 'KHK ',   # TODO: Find out which one should be default
    'kca-kazym': 'KHK ',     # TODO: Pending registration with IETF
    'kca-shuryshk': 'KHS ',  # TODO: Pending registration with IETF
    'kca-vakhi': 'KHV ',     # TODO: Pending registration with IETF
    'hy': 'HYE0',  # HYE0 = Armenian East
    'hy-arevmda': 'HYE ',  # Western Armenian
    'dv': 'DIV ',  # OpenType lists DIV and DHV; DHV is deprecated
    'ga': 'IRI ',
    'ak': 'AKA ',
    'apa': 'ATH ',  # Athapaskan = Apache languages (collection)
    'no': 'NOR ',  # HarfBuzz uses NOR, not NYN
    'chp': 'CHP ',
    'cfm': 'HAL ', # ???
    'rnl': 'QIN ', # ???
    'caf': 'CRR ', # more specific than ATH
    'csw': 'NCR ', # N-Cree = Swampy Cree; Norway House Cree [NHC] seems variant
    'ml': 'MLR ',  # reformed Malayalam
    'ml-pazhaya': 'MAL ',  # traditional Malayalam; TODO: Register tag with IETF
    'cwd': 'DCR ',  # Woods Cree; TCR=Th-Cree seems identical
    'ka': 'KAT ',  # Georgian
    'crx': 'CRR ',  # CRR more specific than ATH
    'emk': 'EMK ',  # EMK more specific than MNK
    'cr': 'CRE ',   # cr is Cree macrolanguage; YCR seems too specific
    'crm': 'CRM ',  # crm = Moose Cree; LCR=L-Cree
    'xal': 'KLM ',  # Kalmyk
    'xal-Mong': 'TOD ', # https://en.wikipedia.org/wiki/Clear_script

    'mlq': 'MLN ',  # TODO: MLN or NNK?
    'el': 'ELL ',   # Greek, use monotonic by default since it is modern
    'el-polyton': 'PGR ',  # Polytonic Greek
    'xsl': 'SSL ',  # TODO: SSL, ATH, SLA?

    # OpenType distinguishes BAL=Balkar and KAR=Karachay.
    # BCP47 has a single code krc=Karachay-Balkar.
    # According to http://www.ethnologue.com/18/language/krc/:
    # "Balkar and Karachay almost identical".
    # Not sure what to do here...
    'krc': 'KAR ',
    'zh': 'ZHS ',   # TODO: ZHH  ZHP  ZHS  ZHT in final step
    'nv': 'NAV ',    # NAV for Navajo is more specific than ATH
    'tut': 'ALT ',  # Altaic languages (collection)

    # Beti [btb] got split by ISO 639-3 into multiple languages,
    # one of which is Fang [fan]. We put 'fan' here so it gets assigned
    # the more specific OpenType language system.
    'fan': 'FAN0',

    # Romanian and Moldovan are the same according to BCP47 but not
    # according to OpenType. Use deprecatd 'mo'?
    'mo': 'MOL ',
    'ro': 'ROM ',
    'ro-MD': 'MOL ',

    # BCP47 sh=Serbo-Croatian is a macrolanguage, and IANA recommends
    # to use sr/hr/bs for most modern use. From a purely typographic
    # perspective, Serbian Cyrillic has some distinct letterforms
    # where as Serbian Latin, Croatian and Bosnian have no special
    # letterforms that would be differnt from mainstream Latin.
    # For this reason, we map the BCP47 code sh to OpenType SRB:
    # Cyrillic fonts will make a distinction from SRB to other languages,
    # but Latin fonts will not make a distinction between Croatian and
    # other Latin languages.
    'sh': 'SRB ',

    'tw': 'TWI ',  # Twi, not Akka
    'zh-HK': 'ZHH ',
}

REVERSE_SPECIAL = {
  'APPH': 'und-fonnapa',
  'IPPH': 'und-fonipa',
  'KGE ': 'ka-Geok',  # Khutsuri Georgian
  'IRT ': 'ga-Latg',  # Irish Traditional
  'ATH ': 'apa',   # Athapaskan --> Apache languages, collection
  'ALT ': 'tut',   # Altaic (collection)
  'ARK ': 'rki',   # Rakhine

  # bhb=Bhili has 3.5M speakers, bhi=Bhilali 1.1M speakers [Wikipedia]
  'BHI ': 'bhb',

  # ble=Balanta-Kenthoe has 400K speakers, bjt=Balanta-Ganja 90K
  'BLN ': 'ble',

  'BTI ': 'btb',   # TODO: btb is deprecated by seven other tags

  # Unclear whether crj=Southern East Cree or crl=Northern East Cree
  # has more speakers.
  'ECR ': 'crj',

  'LRC ': 'lrc',  # Central Luri

  # crx=Carrier has 680 speakers: http://www.ethnologue.com/18/language/crx/
  # caf=Southern Carrier has 500 speakers: http://www.ethnologue.com/18/language/caf/
  'CRR ': 'crx',

  # TODO: When OpenType says "Hindko", doe it mean "Lahnda" [BCP47 lah]?
  # For now, we don't assume so, but it would be good to double-check.
  # hno=Northern Hindko, 1.9M speakers in 1981 [http://www.ethnologue.com/18/language/hno/]
  # hnd=Southern Hindko, 625K speakers in 1981 [http://www.ethnologue.com/18/language/hnd/]
  'HND ': 'hno',

  # OpenType groups swb, wlc, wni, zdj into a single OpenType CMR
  # swb = Maore Comorian, 97K speakers - http://www.ethnologue.com/18/language/swb/
  # wlc = Mwali Comorian, 29K - http://www.ethnologue.com/18/language/wlc/
  # wni = Ndzwani Comorian, 275K - http://www.ethnologue.com/18/language/wni/
  # zdj = Ngazidja Comorian, 300K - http://www.ethnologue.com/18/language/zdj/
  'CMR ': 'zdj',

  # duj = Dhuwal has been depreated for dwu = Dhuwal, dwy = Dhuwaya
  'DUJ ': 'dwu',

  # kss = Southern Kisi, 200K speakers - http://www.ethnologue.com/18/language/kss/
  # kqs = Northern Kissi, 327K speakers - http://www.ethnologue.com/18/language/kqs/
  'KIS ': 'kqs',

  # TODO: https://www.microsoft.com/typography/otspec/languagetags.htm merges
  # two languages called "Ndebele" into a single one. This is surprising
  # because they are not directly related, both according to Ethnologue and
  # to Wikipedia. Find out which one is meant by OpenType.
  # https://en.wikipedia.org/wiki/Zimbabwean_Ndebele_language
  # https://en.wikipedia.org/wiki/Southern_Ndebele_language
  # http://www.ethnologue.com/18/language/nbl/
  # http://www.ethnologue.com/18/language/nde/
  # According to Wikipedia, Zimbabwean Ndebele (BCP47: nd) has 2M L2 speakers
  # while Southern Ndebele (BCP47: nr) has 1.4M. So we pick nd.
  'NDB ': 'nd',

  # According to Ethnologue, Wolane [ISO 639-3: wle] is unwritten;
  # according to Wikipedia, Wolane is a dialect of Silt'e.
  # Therefore, we choose Silt'e [BCP47: stv].
  # http://www.ethnologue.com/18/language/wle/
  # https://en.wikipedia.org/wiki/Silt%27e_language
  'SIG ': 'stv',

  # According to Wikipedia, Tagin [BCP47: tgj] is a dialect of
  # the Nishi language [BCP47: njz]. We therefore pick njz.
  # https://en.wikipedia.org/wiki/Nishi_language
  'NIS ': 'njz',

  # According to Ethnologue (quoted after Wikipedia), there were 150K
  # Shwe [pll] speakers in 1982, 272K Ruching/Palé [pce] speakers in 2000,
  # and 139k Rumai [rbb] speakers at an unrecorded date pll.
  # We therefore pick Ruching/Palé [pce].
  # https://en.wikipedia.org/wiki/Palaung_language
  'PLG ': 'pce',

  # TODO: OpenType puts 'mwg' under QIN (Chin), but this is is a totally
  # different language. Proposal: Remove 'mwg' from QIN in OpenType 1.8.
  # mwg = Aiklep, an Austronesian language - http://www.ethnologue.com/18/language/mwg/
  # TODO: Why is rnl under QIN in OpenType? Could be justified, or maybe
  # just a mistake -- would be good to find out.
  # http://www.ethnologue.com/18/language/rnl/
  # QIN = bgr cbl cmr cnb cnh cnk cnw csh csy ctd czt dao hlt mrh mwg pck rnl sez tcp tcz zom
  #
  # bgr = Cawm Chin, 4.4K speakers - http://www.ethnologue.com/18/language/bgr/
  # cbl = Bualkhaw Chin, 2.5K speakers - http://www.ethnologue.com/18/language/cbl/
  # cmr = Mro-Khimi Chin, 75K speakers - http://www.ethnologue.com/18/language/cmr/
  # cnb = Chinbon Chin, 20K speakers - http://www.ethnologue.com/18/language/cnb/
  # cnh = Haka Chin, 125K speakers - http://www.ethnologue.com/18/language/cnh/
  # cnk =  Khumi Chin, 62K speakers - http://www.ethnologue.com/18/language/cnk/
  # cnw = Ngawn Chin, 15K speakers - http://www.ethnologue.com/18/language/cnw/
  # csh = Asho Chin, 20K speakers - http://www.ethnologue.com/18/language/csh/
  # csy = Siyin Chin, 10K speakers - http://www.ethnologue.com/18/language/csy/
  # ctd = Tedim Chin, 344K speakers - http://www.ethnologue.com/18/language/ctd/
  # czt = Zotung Chin, 40K speakers - http://www.ethnologue.com/18/language/czt/
  # dao = Daai Chin, 37K speakers - http://www.ethnologue.com/18/language/dao/
  # hlt = Matu Chin, 40K speakers - http://www.ethnologue.com/18/language/hlt/
  # mrh = Mara Chin, 55K speakers - http://www.ethnologue.com/18/language/mrh/
  # pck = Paite Chin, 64K speakers - http://www.ethnologue.com/18/language/pck/
  # sez = Senthang Chin, 33K speakers - http://www.ethnologue.com/18/language/sez/
  # tcp = Tawr Chin, 700 speakers - http://www.ethnologue.com/18/language/tcp/
  # tcz = Thado Chin, 269K speakers - http://www.ethnologue.com/18/language/tcz/
  # zom = Zo [a Chin language], 82K speakers - http://www.ethnologue.com/18/language/zom/
  #
  # TODO: For now, we use ctd because it has the most speakers, but it would
  # be good to register a macrolanguage or collection.
  'QIN ': 'ctd',

  'ZHH ': 'zh-HK',
  'ZHP ': 'zh-pinyin',
  'ZHS ': 'zh-Hans',
  'ZHT ': 'zh-Hant',

  'DHV ': 'dv',  # DHV is deprecated in favor of DIV for dv=Maldivian

  # NHC for Norway House Cree is same as N-Cree is same as Swampy Cree
  # (BCP47: csw), but OpenType uses two distinct codes for NCR and NHC.
  # TODO: Find out what OpenType intended with the NHC/NCR distinction.
  'NHC ': 'csw',

  # CRM for Moose Cree, LCR for L-Cree; both seem identical (BCP47: crm).
  # TODO: Find out what OpenType intended with its CRM/LCR distinction.
  'LCR ': 'crm',  # crm = Moose Cree; LCR=L-Cree

  'BAL ': 'krc', # Balkar and Karachay almost identical according to Ethnologue
  # TODO: Still register a variant subtag with IETF for Balkar and Karachay?

  'TWI ': 'tw',  # Twi, needs listing because of Twi vs Akan

  # BCP47 has deprecated mo=Moldavian in favor of ro=Romanian.
  'MOL ': 'ro-MD',
  'ROM ': 'ro',

  'SRB ': 'sr',
}


def read_url(url):
    path = os.path.join(tempfile.gettempdir(),
                        md5.md5(url).hexdigest())
    if not os.path.exists(path):
        stream = urllib.urlopen(url)
        with open(path, 'w') as outfile:
            outfile.write(stream.read())
        stream.close()
    with open(path, 'r') as cachefile:
        return cachefile.read()


def read_opentype():
    result = {}
    #reg = read_url(
    #    'https://www.microsoft.com/typography/otspec/languagetags.htm')
    reg = open('languagetags.htm', 'r').read()
    reg = reg.split('Corresponding ISO 639 ID')[1]
    reg = reg.split('</table')[0]
    for entry in reg.split('<tr')[1:]:
        entry = entry.replace('\n', ' ')
        entry = entry.replace('<p>', ' ')
        entry = entry.replace('</p>', ' ')
        match = re.search(
            r'<td>(.+)</td>\s*<td>(.+)</td>\s*<td>(.+)</td>', entry)
        if not match: continue
        name, langsys, iso = match.groups()
        langsys = (langsys.strip() + '    ')[:4]
        iso = filter(None, [c.strip() for c in iso.split(',')])
        for code in iso:
            result.setdefault(code, set()).add(langsys)
    return result


def read_harfbuzz():
    result = {}
    hb = open('hb-ot-tag.cc', 'r').read()
    hb = hb.split('static const LangTag ot_languages')[1]
    hb = hb.split('};')[0]
    for line in hb.splitlines():
        line = line.strip()
        if line.startswith('/*'): continue
        # {"zum",       HB_TAG('L','R','C',' ')},       /* Kumzari */
        match = re.search(
            r'''{"([a-zA-Z0-9]+)",\s+HB_TAG\('(.)','(.)','(.)','(.)'\)},\s*/\*\s*(.+)\s*\*/''', line)
        if not match: continue
        bcp47, t1, t2, t3, t4, comment = match.groups()
        langsys = ''.join((t1, t2, t3, t4))
        result[bcp47] = langsys
    return result


class TagModernizer:
    def __init__(self):
        self.bcp47_registry = self.read_bcp47_registry()
        self.iso639 = self.read_iso639()
        self.iso639_retirements = self.read_iso639_retirements()
        self.bcp47_collections = set()
        self.bcp47_languages = set()
        for entry in self.bcp47_registry:
            if entry['Type'] == 'language':
                tag = entry['Subtag']
                self.bcp47_languages.add(tag)
                if entry.get('Scope') == 'collection':
                    self.bcp47_collections.add(tag)

    def modernize(self, code):
        modern = set()
        codes = self.iso639_retirements.get(code, {code})
        for c in codes:
            if c in self.bcp47_collections:
                modern.add(c)
                continue
            modern.add(self.iso639[c])
        return modern


    def get_grandfatherings(self):
        result = {}
        for entry in self.bcp47_registry:
            if entry['Type'] == 'grandfathered':
                tag = entry['Tag']
                replacements = result[tag] = set()
                preferred = entry.get('Preferred-Value')
                if preferred:
                    replacements.add(preferred)
                comments = entry.get('Comments', '')
                if comments.startswith('see '):
                    for code in comments[4:].split(','):
                        replacements.add(code)
        return result

    def get_deprecated_languages(self):
        result = {}
        for entry in self.bcp47_registry:
            if entry['Type'] == 'language':
                tag = entry['Subtag']
                replacements = set()
                preferred = entry.get('Preferred-Value')
                if preferred:
                    replacements.add(preferred)
                comments = entry.get('Comments', '')
                if comments.startswith('see '):
                    for code in comments[4:].split(','):
                        replacements.add(code)
                if len(replacements) > 0:
                    result[tag] = replacements
        return result

    def get_macrolanguages(self):
        result = {}
        for entry in self.bcp47_registry:
            if entry['Type'] == 'language':
                tag = entry['Subtag']
                macrolang = entry.get('Macrolanguage')
                if macrolang:
                    result.setdefault(macrolang, set()).add(tag)
        return result

    def read_bcp47_registry(self, ):
        entries = []
        reg = open('language-subtag-registry', 'r').read()    
        for entry in reg.split('%%')[1:]:
            curEntry = {}
            entries.append(curEntry)
            for line in entry.split('\n'):
                if ':' not in line: continue
                key, value = line.split(':', 1)
                curEntry[key] = '\n'.join(
                    filter(None, [curEntry.get(key, ''), value])).strip()
        return entries

    # http://www.unicode.org/repos/cldr/trunk/tools/java/org/unicode/cldr/util/data/iso-639-3.tab
    def read_iso639(self):
        result = {}
        for line in open('iso-639-3.tab', 'r').readlines():
            cols = line.split('\t', 6)
            long, short, name = cols[0], cols[3], cols[-1]
            if not short: short = long
            result[long] = short
        return result


    # http://www.unicode.org/repos/cldr/trunk/tools/java/org/unicode/cldr/util/data/iso-639-3_Retirements.tab
    def read_iso639_retirements(self):
        result = {}
        for line in open('iso-639-3_Retirements.tab', 'r').readlines()[1:]:
            cols = line.split('\t')
            id, replacement, remedy = cols[0], cols[3], cols[4]
            replacements = set(re.findall(r'\[(.+?)\]', remedy))
            if replacement: replacements.add(replacement)
            assert id not in result
            result[id] = replacements
        return result


# Find BCP47 codes whose OpenType equivalent is identical to that of
# their language subtag. Currently, this finds: {kca-kazym no-bok
# zh-guoyu zh-hakka zh-min zh-min-nan zh-xiang}
def find_redundant_codes(mapping):
    redundant = set()
    for code in mapping.keys():
        if '-' in code:
            lang = code.split('-')[0]
            if lang not in ('art', 'i', '*'):
                if mapping[code] == mapping[lang]:
                    redundant.add(code)
    return redundant


def build_reverse_mapping(tags, bcp47_to_opentype):
    deprecated = set(tags.get_deprecated_languages().keys())
    for code in tags.get_grandfatherings().keys():
        deprecated.add(code)
    special = {k: {v} for k, v in REVERSE_SPECIAL.items()}
    for macrolang, sublangs in tags.get_macrolanguages().items():
        langsys = bcp47_to_opentype.get(macrolang)
        if langsys is not None and langsys not in REVERSE_SPECIAL:
            special.setdefault(langsys, set()).add(macrolang)

    result = dict(special)
    for bcp47, langsys in bcp47_to_opentype.items():
        if bcp47 not in deprecated and langsys not in special:
            result.setdefault(langsys, set()).add(bcp47)

    for langsys, bcp47s in sorted(result.items()):
        assert len(bcp47s) == 1, \
            ('Ambiguous mapping: %s --> %s' %
             (langsys,' '.join(sorted(bcp47s))))

    return {k: list(v)[0] for k, v in result.items()}

if __name__ == '__main__':
    tags = TagModernizer()
    bcp47_to_opentype = {k:v for k,v in SPECIAL.items()}
    opentype_languagesystems = set()

    for code_iso639, langsyses in read_opentype().items():
        for langsys in langsyses:
            opentype_languagesystems.add(langsys)
        for code_bcp47 in tags.modernize(code_iso639):
            langsys = SPECIAL.get(code_bcp47)
            if not langsys:
                assert len(langsyses) == 1, code_bcp47
                langsys = sorted(langsyses)[0]
            bcp47_to_opentype[code_bcp47] = langsys

    for macrolang, sublangs in tags.get_macrolanguages().items():
        if macrolang in bcp47_to_opentype:
            langsys = bcp47_to_opentype[macrolang]
            for sublang in sublangs:
                if sublang not in bcp47_to_opentype:
                    bcp47_to_opentype[sublang] = langsys

    for old, new in tags.get_deprecated_languages().items():
        dep = [bcp47_to_opentype[n] for n in new
               if n in bcp47_to_opentype]
        if dep:
            assert len(dep) == 1
            bcp47_to_opentype[old] = dep[0]

    for old, new in tags.get_grandfatherings().items():
        grandfathered = [bcp47_to_opentype[n] for n in new
                         if n in bcp47_to_opentype]
        if grandfathered:
            assert len(grandfathered) == 1
            bcp47_to_opentype[old] = grandfathered[0]

    for code in find_redundant_codes(bcp47_to_opentype):
        del bcp47_to_opentype[code]

    langsyses = set([list(x)[0] for x in read_opentype().values()])
    reverse_mapping = build_reverse_mapping(tags, bcp47_to_opentype)
    missing = langsyses - set(reverse_mapping.keys())
    assert len(missing) == 0, missing

    for langsys in sorted(langsyses):
        bcp47 = reverse_mapping[langsys]
        bcp47_subtags = bcp47.split('-')
        roundtripped = bcp47_to_opentype.get(bcp47)
        if roundtripped == None:
            roundtripped = bcp47_to_opentype.get(
                '-'.join(['*'] + bcp47.split('-')[1:]))
        if langsys in ('DHV ', 'LCR ', 'NHC '): continue
        assert langsys == roundtripped, (langsys, bcp47, roundtripped)

    if False:
      for bcp47, hb_langsys in sorted(read_harfbuzz().items()):
        if bcp47_to_opentype.get(bcp47) != hb_langsys:
            print '%s --> %s, HarfBuzz would give %s' % (
                bcp47, bcp47_to_opentype.get(bcp47), hb_langsys)

    if True:
        for code, langsys in sorted(bcp47_to_opentype.items()):
            print code, langsys
        #for langsys, bcp47 in sorted(reverse_mapping.items()):
        #    print '\t'.join([langsys, bcp47])
