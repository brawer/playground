# coding: utf-8

from __future__ import unicode_literals
import codecs, collections, csv, icu, os


PARTS_OF_SPEECH = {'verb': 'VERB', 'noun': 'NOUN', 'adjective': 'ADJ'}


LOWER = icu.Transliterator.createFromRules(
    'foo-bar', '::lower;', icu.UTransDirection.FORWARD)

CHR_FONIPA = icu.Transliterator.createFromRules(
    'chr-chr_FONIPA', '''

::[[:sc=Cher:][:P:][:M:]];

::upper;

[:P:]+ → ' ';

Ꭰ → a;
Ꭱ → e;
Ꭲ → i;
Ꭳ → o;
Ꭴ → u;
Ꭵ → ə̃;

Ꭶ → ɡa;
Ꭷ → ka;
Ꭸ → ɡe;
Ꭹ → ɡi;
Ꭺ → ɡo;
Ꭻ → ɡu;
Ꭼ → ɡə̃;

Ꭽ → ha;
Ꭾ → he;
Ꭿ → hi;
Ꮀ → ho;
Ꮁ → hu;
Ꮂ → hə̃;

Ꮃ → la;
Ꮄ → le;
Ꮅ → li;
Ꮆ → lo;
Ꮇ → lu;
Ꮈ → lə̃;

Ꮉ → ma;
Ꮊ → me;
Ꮋ → mi;
Ꮌ → mo;
Ꮍ → mu;
Ᏽ → mə̃;

Ꮎ → na;
Ꮏ → hna;
Ꮐ → nah;
Ꮑ → ne;
Ꮒ → ni;
Ꮓ → no;
Ꮔ → nu;
Ꮕ → nə̃;

Ꮖ → kʷa;
Ꮗ → kʷe;
Ꮘ → kʷi;
Ꮙ → kʷo;
Ꮚ → kʷu;
Ꮛ → kʷə̃;

Ꮝ → s;
Ꮜ → sa;
Ꮞ → se;
Ꮟ → si;
Ꮠ → so;
Ꮡ → su;
Ꮢ → sə̃;

Ꮣ → da;
Ꮤ → ta;
Ꮥ → de;
Ꮦ → te;
Ꮧ → di;
Ꮨ → ti;
Ꮩ → do;
Ꮪ → du;
Ꮫ → də̃;

Ꮬ → d͡la;
Ꮭ → t͡ɬa;
Ꮮ → t͡ɬe;
Ꮯ → t͡ɬi;
Ꮰ → t͡ɬo;
Ꮱ → t͡ɬu;
Ꮲ → t͡ɬə̃;

Ꮳ → t͡sa;
Ꮴ → t͡se;
Ꮵ → t͡si;
Ꮶ → t͡so;
Ꮷ → t͡su;
Ꮸ → t͡sə̃;

Ꮹ → wa;
Ꮺ → we;
Ꮻ → wi;
Ꮼ → wo;
Ꮽ → wu;
Ꮾ → wə̃;

Ꮿ → ja;
Ᏸ → je;
Ᏹ → ji;
Ᏺ → jo;
Ᏻ → ju;
Ᏼ → jə̃;

̋ → ˥;
́ → ˦;
̄ → ˧;
̀ → ˧˩;
[ ̌ ̆ ] → ˨˦;
̂ → ˥˧;

[:M:] → ;

#::null;
#a a+ → aː;
#e e+ → eː;
#i i+ → iː;
#o o+ → oː;
#u u+ → uː;
#ə̃ {ə̃}+ → ə̃;

::NFC;
''', icu.UTransDirection.FORWARD)

REVERSE = icu.Transliterator.createFromRules(
    'chr_Latn-chr', '''

::lower;

a → Ꭰ;
e → Ꭱ;
i → Ꭲ;
o → Ꭳ;
u → Ꭴ;
v → Ꭵ;

ga → Ꭶ;
ka → Ꭷ;
ge → Ꭸ;
ke → Ꭸ;
gi → Ꭹ;
ki → Ꭹ;
go → Ꭺ;
ko → Ꭺ;
gu → Ꭻ;
ku → Ꭻ;
gv → Ꭼ;
kv → Ꭼ;

ha → Ꭽ;
he → Ꭾ;
hi → Ꭿ;
ho → Ꮀ;
hu → Ꮁ;
hv → Ꮂ;

la → Ꮃ;
le → Ꮄ;
li → Ꮅ;
lo → Ꮆ;
lu → Ꮇ;
lv → Ꮈ;
l → Ꮅ;

neha → ᏁᎭ;

na → Ꮎ;
hna → Ꮏ;
#→ Ꮐ → nah;
neh → Ꮑ;
ne → Ꮑ;
ni → Ꮒ;
no → Ꮓ;
nu → Ꮔ;
nv → Ꮕ;
n → Ꮒ;

gwa → Ꮖ;
gwe → Ꮗ;
gwi → Ꮘ;
gwo → Ꮙ;
gwu → Ꮚ;
gwv → Ꮛ;

kwa → Ꮖ;
kwe → Ꮗ;
kwi → Ꮘ;
kwo → Ꮙ;
kwu → Ꮚ;
kwv → Ꮛ;

ma → Ꮉ;
me → Ꮊ;
mi → Ꮋ;
mo → Ꮌ;
mu → Ꮍ;
mv → Ᏽ;

sa → Ꮜ;
se → Ꮞ;
si → Ꮟ;
so → Ꮠ;
su → Ꮡ;
sv → Ꮢ;
s → Ꮝ;

dla → Ꮬ;
#dla → Ꮭ;
dle → Ꮮ;
dli → Ꮯ;
dlo → Ꮰ;
dlu → Ꮱ;
dlv → Ꮲ;

da → Ꮣ;
ta → Ꮤ;
de → Ꮥ;
te → Ꮦ;
di → Ꮧ;
ti → Ꮨ;
do → Ꮩ;
to → Ꮩ;
du → Ꮪ;
tu → Ꮪ;
dv → Ꮫ;
tv → Ꮫ;

#hla → Ꮬ;
hla → Ꮭ;
hle → Ꮮ;
hli → Ꮯ;
hlo → Ꮰ;
hlu → Ꮱ;
hlv → Ꮲ;


ja → Ꮳ;
je → Ꮴ;
ji → Ꮵ;
jo → Ꮶ;
ju → Ꮷ;
jv → Ꮸ;

cha → Ꮳ;
che → Ꮴ;
chi → Ꮵ;
cho → Ꮶ;
chu → Ꮷ;
chv → Ꮸ;

wa → Ꮹ;
we → Ꮺ;
wi → Ꮻ;
wo → Ꮼ;
wu → Ꮽ;
wv → Ꮾ;
w → Ꮻ;

ya → Ꮿ;
ye → Ᏸ;
yi → Ᏹ;
yo → Ᏺ;
yu → Ᏻ;
yv → Ᏼ;

k → Ꭶ;
ts → Ꮵ;
d → Ꮨ;
t → Ꮨ;

\? → ʔ;
h → H;

''', icu.UTransDirection.FORWARD)

def make_ipa(form, tone, latin, length, pos):
    ipa = CHR_FONIPA.transliterate(form)
    rev = REVERSE.transliterate(latin)
    rev_ok = (rev.replace('ʔ', '').replace('H', '') == form)
    if rev_ok:
        ipa = CHR_FONIPA.transliterate(rev).replace('H', 'h')

    num_syllables = len(form.replace('Ꮝ', ''))
    if len(length) == num_syllables - 1:
        length = length + '.'
    if num_syllables != len(length):
        return '*** ' + ipa
    marks = [{'-':'ː', '.':''}[c] for c in length]
    tones = tone.split('.')
    tones = [{'1':'¹', '2':'²', '3':'³', '4':'⁴', '23':'²³', '32':'³²', '0':'', '':''}[t] for t in tone.split('.')]
    result = ''
    if len(tones) == num_syllables - 1:
        tones.append('⁴' if pos == 'NOUN' else '¹')
    if len(tones) > num_syllables:
        return '*** ' + ipa
    tones_ok = (len(tones) == num_syllables)
    tones = (tones + ([''] * num_syllables))[:num_syllables]
    for syll in form:
        if syll == 'Ꮝ':
            result = result + 's'
        else:
            result = result + CHR_FONIPA.transliterate(syll) + marks[0] + tones[0]
            marks = marks[1:]
            tones = tones[1:]
    if tones_ok and rev_ok:
        return result
    else:
        return '*** ' + result


def read_words(path):
    print '\t'.join(['no', 'syllabary', 'class', 'suspicious', 'ipa', 'length', 'tone', 'entry']).encode('utf-8')
    poscount = collections.Counter()
    with open(path, 'rb') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        for item in reader:
            form = item['syllabary'].decode('utf-8').strip()
            form_number = item['no'].strip()
            if not form or form == '0':
                # Missing for 47 entries
                continue
            if not form_number:
                # Missing for 7: ᎦᏃᎭᎵᏙᎯ ᎠᏂᏃᎭᎵᏙᎯ ᏗᏝᏬᏚᎭᎢ ᏧᎵᏍᏚᎢᏓ ᏧᎵᏍᎨᏓ ᏧᏬᎵᏗ ᏧᏲᎢ
                continue
            lemma, subid = map(int, form_number.split('-'))
            lemma = '%d' % lemma
            pos = PARTS_OF_SPEECH.get(item['class'], 'X')
            tone = item['tone'].strip()
            length = item['length'].strip()
            latin = item['entry'].strip()
            num_words = len(form.split())
            if num_words == len(length.split()) and num_words == len(tone.split()) and num_words == len(latin.split()):
                ipa = ' '.join([make_ipa(w, t, lat, l, pos)
                                for w, t, lat, l in zip(form.split(), tone.split(), latin.split(), length.split())])
            else:
                ipa = '*** ' + CHR_FONIPA.transliterate(form)
            tricky = '*' in ipa
            if tricky:
                ipa = ' '.join(ipa.replace('*', '').split())
                tricky = '***'
            else:
                tricky = ''
            print '\t'.join([form_number, form, pos, tricky, ipa, length, tone, latin]).encode('utf-8')
            poscount[pos] += 1


if __name__ == '__main__':
    words_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data', 'chr', 'words.csv')
    read_words(words_path)
