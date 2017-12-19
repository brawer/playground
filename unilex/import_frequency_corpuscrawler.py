# coding: utf-8

from __future__ import print_function, unicode_literals
import codecs, icu, os, re, shutil, time, unicodedata, urllib


CACHE_DIR = '/tmp/unilex-import-frequency'
REPO_URL = 'https://github.com/googlei18n/corpuscrawler.git'


# For these languages, we take word counts from different sources
# than corpus crawler.
WORD_FREQUENCY_OVERRIDES = {
    'vec': ('https://raw.githubusercontent.com/brawer/playground/master/'
            'unilex/data/vec/frequency.txt'),
}


def fetch_git_repo():
    repo_path = os.path.join(CACHE_DIR, 'corpuscrawler')
    if not os.path.exists(repo_path):
        os.system('git clone %s %s' % (REPO_URL, repo_path))
    working_dir = os.getcwd()
    os.chdir(repo_path)
    os.system('git fetch --all --prune')
    os.system('git rebase origin/master')
    os.chdir(working_dir)
    return repo_path


def get_available_languages():
    repo_path = fetch_git_repo()
    with open(os.path.join(repo_path, 'README.md'), 'r') as readme_file:
        readme = readme_file.read().decode('utf-8')
    available = {
        lang: url
        for url, lang in re.findall(
                '(http://www.gstatic.com/i18n/corpora/'
                'wordcounts/([^\.]+).txt)', readme)}
    available.update(WORD_FREQUENCY_OVERRIDES)
    return available


def get_frequencies(lang, url):
    local_path = os.path.join(CACHE_DIR, '%s.txt' % lang)
    if not os.path.exists(local_path):
        time.sleep(1.0)
        content = urllib.urlopen(url).read()
        with open(local_path, 'w') as out:
            out.write(content)
    with open(local_path, 'r') as freqfile:
        content = freqfile.read().decode('utf-8')
    forms = []
    corpus_size = 0
    for line in content.splitlines():
        line = line.strip()
        if not line or line[0] == '#':
            continue
        count, form = line.split('\t')
        count = int(count)
        form = unicodedata.normalize('NFC', form.strip())
        if form[0] not in '*_0123456789':
            forms.append((form, count))
            corpus_size += count
    factor = 1e9 / corpus_size
    forms = [(form, int(count * factor)) for form, count in forms]
    locale = icu.Locale(lang)
    collator = icu.Collator.createInstance(locale)
    def compare(a, b):
        if collator.greater(a[0], b[0]):
            return 1
        elif collator.greaterOrEqual(a[0], b[0]):
            return cmp(a[1], b[1])
        else:
            return -1
    forms.sort(cmp=compare)
    return forms, corpus_size


if __name__ == '__main__':
    out_path = os.path.join(CACHE_DIR, 'out')
    if os.path.exists(out_path):
        shutil.rmtree(out_path)
    for lang, url in sorted(get_available_languages().items()):
        freq, corpus_size = get_frequencies(lang, url)
        print(lang, sum(c for _,c in freq))
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        with open(os.path.join(out_path, '%s.txt' % lang), 'w') as out:
            out.write('Form\tFrequency\n'
                      '\n'
                      '# SPDX-License-Identifier: Unicode-DFS-2016\n'
                      '# Corpus-Size: %d\n'
                      '\n' % corpus_size)
            for form, frequency in freq:
                out.write(form.encode('utf-8'))
                out.write('\t')
                out.write(str(frequency))
                out.write('\n')
    print('Done. Results: %s' % out_path)
