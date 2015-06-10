ttfvary
=======

The `ttfvary` tool runs a TrueType font with
[glyph variations](http://en.wikipedia.org/wiki/Multiple_master_fonts)
through the MacOS X CoreText library, writing a PostScript document
to standard output. For every glyph in the input font, the output
document contains a page that shows the glyph’s outline in 350 variants.

How to build and run:
`$ make -s && ./ttfvary -font /Library/Fonts/Skia.ttf >out.ps`

<img src="https://raw.githubusercontent.com/brawer/playground/master/fonts/ttfvary/Otilde.png" width="513" height="706" alt="Screenshot of output for one glyph" />


