ttfvary
=======

The `ttfvary` tool runs a TrueType font with
[glyph variations](http://en.wikipedia.org/wiki/Multiple_master_fonts)
through the MacOS X CoreText library, and writes PostScript document
to standard output. For every glyph in the input font, the output document contains a page that shows the glyph’s outline in 350 variants.

This tool was quite helpful for developing the “gvar” handling in
[fonttools](https://github.com/behdad/fonttools).

To build and run the tool:
`$ make -s && ./ttfvary -font /Library/Fonts/Skia.ttf >out.ps`

![Image of output](https://raw.githubusercontent.com/brawer/playground/master/fonts/ttfvary/Otilde.png)

