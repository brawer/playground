import re, unicodedata

for line in open('x'):
    if 'Expected "TODO" but got' not in line: continue
    line = unicodedata.normalize('NFC', line.strip().decode('utf-8'))
    line = line.encode('utf-8')
    got, orig = re.match(r'.*got "(.+?)" for "(.+?)"', line.strip()).groups()
    print '\t'.join([orig, got])
