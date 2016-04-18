# ShowVariationInstanceNames

This tool queries MacOS X CoreText for the PostScript names of
instances of variation fonts.


## Limitations

Currently, this tool make built-in assumptions about the number and
range of design axes, and also about the named instances that are
present in the font. These assumptions happen to match Apple’s “Skia”
font. Of course, a proper implementation would query CoreText, which
would then get this information from the font’s `fvar` table. If anyone
wants to implement this, feel free to do so; simply send me a GitHub pull
request.


## Build and run

```sh
$ git clone https://github.com/brawer/playground.git
$ cd playground/fonts/ShowVariationInstanceNames
$ make && ./ShowVariationInstanceNames -font /Library/Fonts/Skia.ttf
```


## Output

On MacOS X 10.11.4, this tool prints the following output for the version
of “Skia” whose SHA-1 hash is `a5361164b6f41f5998f5ac8618ecf900f3c4ad37`:
```
wght:0.48000 wdth:0.70000 Skia-Regular_Light-Condensed
wght:0.48000 wdth:1.00000 Skia-Regular_Light
wght:0.48000 wdth:1.29999 Skia-Regular_Light-Extended
wght:1.00000 wdth:0.61998 Skia-Regular_Condensed
wght:1.00000 wdth:1.00000 Skia-Regular
wght:1.00000 wdth:1.29999 Skia-Regular_Extended
wght:1.95000 wdth:1.00000 Skia-Regular_Bold
wght:3.00000 wdth:0.70000 Skia-Regular_Black-Condensed
wght:3.20000 wdth:1.00000 Skia-Regular_Black
wght:3.20000 wdth:1.29999 Skia-Regular_Black-Extended

wght:0.50000 wdth:0.70000 Skia-Regular_wght8000_wdthB333
wght:0.50000 wdth:0.80000 Skia-Regular_wght8000_wdthCCCC
wght:0.50000 wdth:0.90000 Skia-Regular_wght8000_wdthE666
wght:0.50000 wdth:1.00000 Skia-Regular_wght8000_wdth10000
wght:0.50000 wdth:1.10000 Skia-Regular_wght8000_wdth11999
wght:0.50000 wdth:1.20000 Skia-Regular_wght8000_wdth13333
wght:0.60000 wdth:0.70000 Skia-Regular_wght9999_wdthB333
wght:0.60000 wdth:0.80000 Skia-Regular_wght9999_wdthCCCC
wght:0.60000 wdth:0.90000 Skia-Regular_wght9999_wdthE666
wght:0.60000 wdth:1.00000 Skia-Regular_wght9999_wdth10000
wght:0.60000 wdth:1.10000 Skia-Regular_wght9999_wdth11999
wght:0.60000 wdth:1.20000 Skia-Regular_wght9999_wdth13333
wght:0.70000 wdth:0.70000 Skia-Regular_wghtB333_wdthB333
wght:0.70000 wdth:0.80000 Skia-Regular_wghtB333_wdthCCCC
wght:0.70000 wdth:0.90000 Skia-Regular_wghtB333_wdthE666
wght:0.70000 wdth:1.00000 Skia-Regular_wghtB333_wdth10000
wght:0.70000 wdth:1.10000 Skia-Regular_wghtB333_wdth11999
wght:0.70000 wdth:1.20000 Skia-Regular_wghtB333_wdth13333
wght:0.80000 wdth:0.70000 Skia-Regular_wghtCCCC_wdthB333
wght:0.80000 wdth:0.80000 Skia-Regular_wghtCCCC_wdthCCCC
wght:0.80000 wdth:0.90000 Skia-Regular_wghtCCCC_wdthE666
wght:0.80000 wdth:1.00000 Skia-Regular_wghtCCCC_wdth10000
wght:0.80000 wdth:1.10000 Skia-Regular_wghtCCCC_wdth11999
wght:0.80000 wdth:1.20000 Skia-Regular_wghtCCCC_wdth13333
wght:0.90000 wdth:0.70000 Skia-Regular_wghtE666_wdthB333
wght:0.90000 wdth:0.80000 Skia-Regular_wghtE666_wdthCCCC
wght:0.90000 wdth:0.90000 Skia-Regular_wghtE666_wdthE666
wght:0.90000 wdth:1.00000 Skia-Regular_wghtE666_wdth10000
wght:0.90000 wdth:1.10000 Skia-Regular_wghtE666_wdth11999
wght:0.90000 wdth:1.20000 Skia-Regular_wghtE666_wdth13333
wght:1.00000 wdth:0.70000 Skia-Regular_wght10000_wdthB333
wght:1.00000 wdth:0.80000 Skia-Regular_wght10000_wdthCCCC
wght:1.00000 wdth:0.90000 Skia-Regular_wght10000_wdthE666
wght:1.00000 wdth:1.00000 Skia-Regular
wght:1.00000 wdth:1.10000 Skia-Regular_wght10000_wdth11999
wght:1.00000 wdth:1.20000 Skia-Regular_wght10000_wdth13333
wght:1.10000 wdth:0.70000 Skia-Regular_wght11999_wdthB333
wght:1.10000 wdth:0.80000 Skia-Regular_wght11999_wdthCCCC
wght:1.10000 wdth:0.90000 Skia-Regular_wght11999_wdthE666
wght:1.10000 wdth:1.00000 Skia-Regular_wght11999_wdth10000
wght:1.10000 wdth:1.10000 Skia-Regular_wght11999_wdth11999
wght:1.10000 wdth:1.20000 Skia-Regular_wght11999_wdth13333
wght:1.20000 wdth:0.70000 Skia-Regular_wght13333_wdthB333
wght:1.20000 wdth:0.80000 Skia-Regular_wght13333_wdthCCCC
wght:1.20000 wdth:0.90000 Skia-Regular_wght13333_wdthE666
wght:1.20000 wdth:1.00000 Skia-Regular_wght13333_wdth10000
wght:1.20000 wdth:1.10000 Skia-Regular_wght13333_wdth11999
wght:1.20000 wdth:1.20000 Skia-Regular_wght13333_wdth13333
wght:1.30000 wdth:0.70000 Skia-Regular_wght14CCC_wdthB333
wght:1.30000 wdth:0.80000 Skia-Regular_wght14CCC_wdthCCCC
wght:1.30000 wdth:0.90000 Skia-Regular_wght14CCC_wdthE666
wght:1.30000 wdth:1.00000 Skia-Regular_wght14CCC_wdth10000
wght:1.30000 wdth:1.10000 Skia-Regular_wght14CCC_wdth11999
wght:1.30000 wdth:1.20000 Skia-Regular_wght14CCC_wdth13333
wght:1.40000 wdth:0.70000 Skia-Regular_wght16666_wdthB333
wght:1.40000 wdth:0.80000 Skia-Regular_wght16666_wdthCCCC
wght:1.40000 wdth:0.90000 Skia-Regular_wght16666_wdthE666
wght:1.40000 wdth:1.00000 Skia-Regular_wght16666_wdth10000
wght:1.40000 wdth:1.10000 Skia-Regular_wght16666_wdth11999
wght:1.40000 wdth:1.20000 Skia-Regular_wght16666_wdth13333
wght:1.50000 wdth:0.70000 Skia-Regular_wght18000_wdthB333
wght:1.50000 wdth:0.80000 Skia-Regular_wght18000_wdthCCCC
wght:1.50000 wdth:0.90000 Skia-Regular_wght18000_wdthE666
wght:1.50000 wdth:1.00000 Skia-Regular_wght18000_wdth10000
wght:1.50000 wdth:1.10000 Skia-Regular_wght18000_wdth11999
wght:1.50000 wdth:1.20000 Skia-Regular_wght18000_wdth13333
wght:1.60000 wdth:0.70000 Skia-Regular_wght19999_wdthB333
wght:1.60000 wdth:0.80000 Skia-Regular_wght19999_wdthCCCC
wght:1.60000 wdth:0.90000 Skia-Regular_wght19999_wdthE666
wght:1.60000 wdth:1.00000 Skia-Regular_wght19999_wdth10000
wght:1.60000 wdth:1.10000 Skia-Regular_wght19999_wdth11999
wght:1.60000 wdth:1.20000 Skia-Regular_wght19999_wdth13333
wght:1.70000 wdth:0.70000 Skia-Regular_wght1B333_wdthB333
wght:1.70000 wdth:0.80000 Skia-Regular_wght1B333_wdthCCCC
wght:1.70000 wdth:0.90000 Skia-Regular_wght1B333_wdthE666
wght:1.70000 wdth:1.00000 Skia-Regular_wght1B333_wdth10000
wght:1.70000 wdth:1.10000 Skia-Regular_wght1B333_wdth11999
wght:1.70000 wdth:1.20000 Skia-Regular_wght1B333_wdth13333
wght:1.80000 wdth:0.70000 Skia-Regular_wght1CCCC_wdthB333
wght:1.80000 wdth:0.80000 Skia-Regular_wght1CCCC_wdthCCCC
wght:1.80000 wdth:0.90000 Skia-Regular_wght1CCCC_wdthE666
wght:1.80000 wdth:1.00000 Skia-Regular_wght1CCCC_wdth10000
wght:1.80000 wdth:1.10000 Skia-Regular_wght1CCCC_wdth11999
wght:1.80000 wdth:1.20000 Skia-Regular_wght1CCCC_wdth13333
wght:1.90000 wdth:0.70000 Skia-Regular_wght1E666_wdthB333
wght:1.90000 wdth:0.80000 Skia-Regular_wght1E666_wdthCCCC
wght:1.90000 wdth:0.90000 Skia-Regular_wght1E666_wdthE666
wght:1.90000 wdth:1.00000 Skia-Regular_wght1E666_wdth10000
wght:1.90000 wdth:1.10000 Skia-Regular_wght1E666_wdth11999
wght:1.90000 wdth:1.20000 Skia-Regular_wght1E666_wdth13333
wght:2.00000 wdth:0.70000 Skia-Regular_wght20000_wdthB333
wght:2.00000 wdth:0.80000 Skia-Regular_wght20000_wdthCCCC
wght:2.00000 wdth:0.90000 Skia-Regular_wght20000_wdthE666
wght:2.00000 wdth:1.00000 Skia-Regular_wght20000_wdth10000
wght:2.00000 wdth:1.10000 Skia-Regular_wght20000_wdth11999
wght:2.00000 wdth:1.20000 Skia-Regular_wght20000_wdth13333
wght:2.10000 wdth:0.70000 Skia-Regular_wght21999_wdthB333
wght:2.10000 wdth:0.80000 Skia-Regular_wght21999_wdthCCCC
wght:2.10000 wdth:0.90000 Skia-Regular_wght21999_wdthE666
wght:2.10000 wdth:1.00000 Skia-Regular_wght21999_wdth10000
wght:2.10000 wdth:1.10000 Skia-Regular_wght21999_wdth11999
wght:2.10000 wdth:1.20000 Skia-Regular_wght21999_wdth13333
wght:2.20000 wdth:0.70000 Skia-Regular_wght23333_wdthB333
wght:2.20000 wdth:0.80000 Skia-Regular_wght23333_wdthCCCC
wght:2.20000 wdth:0.90000 Skia-Regular_wght23333_wdthE666
wght:2.20000 wdth:1.00000 Skia-Regular_wght23333_wdth10000
wght:2.20000 wdth:1.10000 Skia-Regular_wght23333_wdth11999
wght:2.20000 wdth:1.20000 Skia-Regular_wght23333_wdth13333
wght:2.30000 wdth:0.70000 Skia-Regular_wght24CCC_wdthB333
wght:2.30000 wdth:0.80000 Skia-Regular_wght24CCC_wdthCCCC
wght:2.30000 wdth:0.90000 Skia-Regular_wght24CCC_wdthE666
wght:2.30000 wdth:1.00000 Skia-Regular_wght24CCC_wdth10000
wght:2.30000 wdth:1.10000 Skia-Regular_wght24CCC_wdth11999
wght:2.30000 wdth:1.20000 Skia-Regular_wght24CCC_wdth13333
wght:2.40000 wdth:0.70000 Skia-Regular_wght26666_wdthB333
wght:2.40000 wdth:0.80000 Skia-Regular_wght26666_wdthCCCC
wght:2.40000 wdth:0.90000 Skia-Regular_wght26666_wdthE666
wght:2.40000 wdth:1.00000 Skia-Regular_wght26666_wdth10000
wght:2.40000 wdth:1.10000 Skia-Regular_wght26666_wdth11999
wght:2.40000 wdth:1.20000 Skia-Regular_wght26666_wdth13333
wght:2.50000 wdth:0.70000 Skia-Regular_wght27FFF_wdthB333
wght:2.50000 wdth:0.80000 Skia-Regular_wght27FFF_wdthCCCC
wght:2.50000 wdth:0.90000 Skia-Regular_wght27FFF_wdthE666
wght:2.50000 wdth:1.00000 Skia-Regular_wght27FFF_wdth10000
wght:2.50000 wdth:1.10000 Skia-Regular_wght27FFF_wdth11999
wght:2.50000 wdth:1.20000 Skia-Regular_wght27FFF_wdth13333
wght:2.60000 wdth:0.70000 Skia-Regular_wght29999_wdthB333
wght:2.60000 wdth:0.80000 Skia-Regular_wght29999_wdthCCCC
wght:2.60000 wdth:0.90000 Skia-Regular_wght29999_wdthE666
wght:2.60000 wdth:1.00000 Skia-Regular_wght29999_wdth10000
wght:2.60000 wdth:1.10000 Skia-Regular_wght29999_wdth11999
wght:2.60000 wdth:1.20000 Skia-Regular_wght29999_wdth13333
wght:2.70000 wdth:0.70000 Skia-Regular_wght2B333_wdthB333
wght:2.70000 wdth:0.80000 Skia-Regular_wght2B333_wdthCCCC
wght:2.70000 wdth:0.90000 Skia-Regular_wght2B333_wdthE666
wght:2.70000 wdth:1.00000 Skia-Regular_wght2B333_wdth10000
wght:2.70000 wdth:1.10000 Skia-Regular_wght2B333_wdth11999
wght:2.70000 wdth:1.20000 Skia-Regular_wght2B333_wdth13333
wght:2.80000 wdth:0.70000 Skia-Regular_wght2CCCC_wdthB333
wght:2.80000 wdth:0.80000 Skia-Regular_wght2CCCC_wdthCCCC
wght:2.80000 wdth:0.90000 Skia-Regular_wght2CCCC_wdthE666
wght:2.80000 wdth:1.00000 Skia-Regular_wght2CCCC_wdth10000
wght:2.80000 wdth:1.10000 Skia-Regular_wght2CCCC_wdth11999
wght:2.80000 wdth:1.20000 Skia-Regular_wght2CCCC_wdth13333
wght:2.90000 wdth:0.70000 Skia-Regular_wght2E666_wdthB333
wght:2.90000 wdth:0.80000 Skia-Regular_wght2E666_wdthCCCC
wght:2.90000 wdth:0.90000 Skia-Regular_wght2E666_wdthE666
wght:2.90000 wdth:1.00000 Skia-Regular_wght2E666_wdth10000
wght:2.90000 wdth:1.10000 Skia-Regular_wght2E666_wdth11999
wght:2.90000 wdth:1.20000 Skia-Regular_wght2E666_wdth13333
wght:3.00000 wdth:0.70000 Skia-Regular_Black-Condensed
wght:3.00000 wdth:0.80000 Skia-Regular_wght2FFFF_wdthCCCC
wght:3.00000 wdth:0.90000 Skia-Regular_wght2FFFF_wdthE666
wght:3.00000 wdth:1.00000 Skia-Regular_wght2FFFF_wdth10000
wght:3.00000 wdth:1.10000 Skia-Regular_wght2FFFF_wdth11999
wght:3.00000 wdth:1.20000 Skia-Regular_wght2FFFF_wdth13333
wght:3.10000 wdth:0.70000 Skia-Regular_wght31999_wdthB333
wght:3.10000 wdth:0.80000 Skia-Regular_wght31999_wdthCCCC
wght:3.10000 wdth:0.90000 Skia-Regular_wght31999_wdthE666
wght:3.10000 wdth:1.00000 Skia-Regular_wght31999_wdth10000
wght:3.10000 wdth:1.10000 Skia-Regular_wght31999_wdth11999
wght:3.10000 wdth:1.20000 Skia-Regular_wght31999_wdth13333
```
