CLDR playground
===============

This is my playground for small clean-ups of various data files.
I plan contributing these files to the
[Unicode CLDR](http://cldr.unicode.org/) project, and these
scripts here help me ensuring that my submissions are reaonable.

To run the scripts on a Debian machine:

    $ sudo apt-get install libicu-dev python-pyicu
    $ git clone https://github.com/brawer/playground.git
    $ cd playground/cldr
    $ python check_translit_hy.py   # Armenian
    $ python check_translit_my.py   # Burmese
    $ python check_translit_sat.py  # Santali
    $ python check_translit_si.py   # Sinhala
