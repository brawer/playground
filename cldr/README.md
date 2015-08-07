CLDR playground
===============

This is my playground (or staging area) for small clean-ups to various
data files for the [Unicode CLDR](http://cldr.unicode.org/) project.
Once the files are in a reasonable state, I will send them upstream
for addition to Unicode CLDR.

To run the scripts on a Debian machine:

    $ sudo apt-get install libicu-dev python-pyicu
    $ git clone https://github.com/brawer/playground.git
    $ cd playground/cldr
    $ python check_translit_am.py          # Amharic
    $ python check_translit_hy.py          # Armenian
    $ python check_translit_my.py          # Burmese
    $ python check_translit_rm_SURSILV.py  # Rumantsch Sursilvan
    $ python check_translit_sat.py         # Santali
    $ python check_translit_si.py          # Sinhala
