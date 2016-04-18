// MacOS X tool for showing PostScript names of instances of variation fonts,
// as assigned by the Apple CoreText library.
//
// Copyright 2016 by Sascha Brawer <sascha@brawer.ch>
// Licensed unter the Apache 2.0 license, see LICENSE.md

#include <stdio.h>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "ApplicationServices/ApplicationServices.h"
#include "CoreGraphics/CoreGraphics.h"
#include "CoreText/CoreText.h"
#include "Foundation/Foundation.h"

class Font {
 public:
  static Font* FromFile(const char* path);
  ~Font();

  typedef std::map<std::string, float> VariationMap;
  Font* MakeVariation(const VariationMap& variation) const;
  std::string GetPostScriptName() const;

 private:
  Font(CGFontRef cgfont);

  CGDataProviderRef provider_;
  CGFontRef cgfont_;
  CTFontRef ctfont_;
};

Font* Font::FromFile(const char* path) {
  CGDataProviderRef provider = CGDataProviderCreateWithFilename(path);
  if (provider == NULL) {
    return NULL;
  }

  CGFontRef font = CGFontCreateWithDataProvider(provider);
  if (font == NULL) {
    CGDataProviderRelease(provider);
    return NULL;
  }

  Font* result = new Font(font);
  CGDataProviderRelease(provider);
  return result;
}

Font::Font(CGFontRef cgfont)
  : cgfont_(cgfont),
    ctfont_(CTFontCreateWithGraphicsFont(cgfont_, 16, NULL, NULL)) {
  CGFontRetain(cgfont);
}

Font::~Font() {
  if (ctfont_ != NULL) {
    CFRelease(ctfont_);
  }

  if (cgfont_ != NULL) {
    CGFontRelease(cgfont_);
  }
}

Font* Font::MakeVariation(const VariationMap& variation) const {
  NSMutableDictionary* dict = [NSMutableDictionary dictionary];
  for (VariationMap::const_iterator iter = variation.begin();
       iter != variation.end(); ++iter) {
    NSString* key = [NSString stringWithUTF8String:iter->first.c_str()];
    NSNumber* value = [NSNumber numberWithFloat:iter->second];
    [dict setObject:value forKey:key];
  }
  CGFontRef gvarFont =
      CGFontCreateCopyWithVariations(cgfont_,
                                     reinterpret_cast<CFDictionaryRef>(dict));
  return new Font(gvarFont);
}

std::string Font::GetPostScriptName() const {
  if (cgfont_ == NULL) {
    return "";
  }

  std::string result;
  const NSString* nsname =
      reinterpret_cast<const NSString*>(CGFontCopyPostScriptName(cgfont_));
  result.assign([nsname UTF8String]);
  [nsname release];
  return result;
}

bool HasCoreText() {
  return ((&CTGetCoreTextVersion != NULL) &&
          (CTGetCoreTextVersion() >= kCTVersionNumber10_5));
}

void PrintPostScriptName(Font* font, float weight, float width) {
  Font::VariationMap variations;
  variations["Weight"] = weight;
  variations["Width"] = width;
  std::unique_ptr<Font> instance(font->MakeVariation(variations));
  printf("wght:%1.5f wdth:%1.5f %s\n", weight, width,
	 instance->GetPostScriptName().c_str());
}

int main(int argc, const char * argv[]) {
  if (!HasCoreText()) {
    fprintf(stderr, "CoreText not available");
    return 1;
  }

  NSAutoreleasePool* pool = [[NSAutoreleasePool alloc] init];
  NSUserDefaults* args = [NSUserDefaults standardUserDefaults];
  NSString* fontPath = [args stringForKey:@"font"];
  if (!fontPath) {
    fprintf(stderr, "usage: %s -font /Library/Fonts/Skia.ttf\n", argv[0]);
    return 1;
  }

  std::unique_ptr<Font> font(Font::FromFile([fontPath UTF8String]));
  if (!font.get()) {
    fprintf(stderr, "cannot load font from %s\n", [fontPath UTF8String]);
    return 1;
  }

  PrintPostScriptName(font.get(), 0.48, 0.7);  // Light Condensed
  PrintPostScriptName(font.get(), 0.48, 1.0);  // Light
  PrintPostScriptName(font.get(), 0.48, 1.29999);  // Light Extended
  PrintPostScriptName(font.get(), 1.0, 0.61998);  // (Regular) Condensed
  PrintPostScriptName(font.get(), 1.0, 1.0);  // Regular
  PrintPostScriptName(font.get(), 1.0, 1.29999);  // (Regular) Extended
  PrintPostScriptName(font.get(), 1.95, 1.0);  // Bold
  PrintPostScriptName(font.get(), 3.0, 0.7);  // Black Condensed
  PrintPostScriptName(font.get(), 3.2, 1.0);  // Black
  PrintPostScriptName(font.get(), 3.2, 1.29999);  // Black Extended

  printf("\n");
  for (float weight = 0.5; weight <= 3.1; weight += 0.1) {
    for (float width = 0.7; width <= 1.3; width += 0.1) {
      PrintPostScriptName(font.get(), weight, width);
    }
  }

  return 0;
}
