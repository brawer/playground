#include <stdio.h>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "ApplicationServices/ApplicationServices.h"
#include "CoreGraphics/CoreGraphics.h"
#include "CoreText/CoreText.h"
#include "Foundation/Foundation.h"

class Pen {
 public:
  virtual void MoveTo(float x, float y) = 0;
  virtual void LineTo(float x, float y) = 0;
  virtual void QuadTo(float ax, float ay, float x, float y) = 0;
  virtual void CurveTo(float ax, float ay, float bx, float by,
                       float x, float y) = 0;
  virtual void ClosePath() = 0;
};

class Font {
 public:
  static Font* FromFile(const char* path);
  ~Font();

  typedef std::map<std::string, float> VariationMap;
  Font* MakeVariation(const VariationMap& variation) const;

  std::string GetPostScriptName() const;

  int GetGlyphCount() const;
  std::string GetGlyphName(int glyph) const;
  void DrawGlyphOutline(int glyph, Pen* pen) const;

 private:
  Font(CGFontRef cgfont);
  static void VisitPathElement_(void* data, const CGPathElement* element);

  CGDataProviderRef provider_;
  CGFontRef cgfont_;
  CTFontRef ctfont_;
};

class PostScriptPen : public virtual Pen {
 public:
  virtual void MoveTo(float x, float y) { printf("%.5f %.5f moveto\n", x, y); }
  virtual void LineTo(float x, float y) { printf("%.5f %.5f lineto\n", x, y); }

  virtual void QuadTo(float ax, float ay, float x, float y) {
    printf("%.5f %.5f %.5f %.5f quadto\n", ax, ay, x, y);
  }

  virtual void CurveTo(float ax, float ay, float bx, float by,
                       float x, float y) {
    printf("%.5f %.5f %.5f %.5f %.5f %.5f curveto\n", ax, ay, bx, by, x, y);
  }

  virtual void ClosePath() { printf("closepath\n"); }
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

int Font::GetGlyphCount() const {
  if (ctfont_) {
    return CTFontGetGlyphCount(ctfont_);
  } else {
    return 0;
  }
}

std::string Font::GetGlyphName(int glyph) const {
  if (cgfont_ == NULL) {
    return "";
  }

  std::string result;
  const NSString* nsname = reinterpret_cast<const NSString*>(
      CGFontCopyGlyphNameForGlyph(cgfont_, glyph));
  if (!nsname) {
    return "";
  }

  result.assign([nsname UTF8String]);
  [nsname release];
  return result;
}

void Font::DrawGlyphOutline(int glyph, Pen* pen) const {
  CGPathRef path = CTFontCreatePathForGlyph(ctfont_, glyph, NULL);
  if (!path) {
    return;
  }

  CGPathApply(path, reinterpret_cast<void*>(pen), &Font::VisitPathElement_);
  CGPathRelease(path);
}

void Font::VisitPathElement_(void* data, const CGPathElement* element) {
  Pen* pen = reinterpret_cast<Pen*>(data);
  switch (element->type) {
  case kCGPathElementMoveToPoint:
    pen->MoveTo(element->points[0].x, element->points[0].y);
    break;

  case kCGPathElementAddLineToPoint:
    pen->LineTo(element->points[0].x, element->points[0].y);
    break;

  case kCGPathElementAddQuadCurveToPoint:
    pen->QuadTo(element->points[0].x, element->points[0].y,
                element->points[1].x, element->points[1].y);
    break;

  case kCGPathElementAddCurveToPoint:
    pen->CurveTo(element->points[0].x, element->points[0].y,
                 element->points[1].x, element->points[1].y,
                 element->points[2].x, element->points[2].y);
    break;

  case kCGPathElementCloseSubpath:
    pen->ClosePath();
    break;
  }
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

int main(int argc, const char * argv[]) {
  if (!HasCoreText()) {
    fprintf(stderr, "CoreText not available");
    return 1;
  }

  NSAutoreleasePool* pool = [[NSAutoreleasePool alloc] init];
  NSUserDefaults* args = [NSUserDefaults standardUserDefaults];
  NSString* fontPath = [args stringForKey:@"font"];
  if (!fontPath) {
    fprintf(stderr, "usage: ttfvary -font SomeFont.ttf\n");
    return 1;
  }

  Font* font = Font::FromFile([fontPath UTF8String]);
  if (!font) {
    fprintf(stderr, "cannot load font from %s\n", [fontPath UTF8String]);
    return 1;
  }

  printf("%%!PS-Adobe-2.0\n%%%%EndComments\n");
  printf("%%%%BeginSetup\n");
  printf("/quadto {\n"
         "  /cy exch def /cx exch def\n"
         "  /by exch def /bx exch def\n"
         "  currentpoint /ay exch def /ax exch def\n"
         "  %% P := A + (B - A) * 2/3\n"
         "  /px bx ax sub 2 mul 3 div ax add def\n"
         "  /py by ay sub 2 mul 3 div ay add def\n"
         "  %% Q := C + (B - C) * 2/3\n"
         "  /qx bx cx sub 2 mul 3 div cx add def\n"
         "  /qy by cy sub 2 mul 3 div cy add def\n"
         "  px py qx qy cx cy curveto\n"
         "} def\n");
  printf("%%%%EndSetup\n");

  std::vector<Font*> gvarFonts;
  for (float width = 0.7; width <= 1.3; width += 0.05) {
    for (float weight = 0.5; weight <= 3.1; weight += 0.1) {
	Font::VariationMap variations;
	variations["Width"] = width;
	variations["Weight"] = weight;
	gvarFonts.push_back(font->MakeVariation(variations));
    }
  }

  const int numGlyphs = font->GetGlyphCount();
  for (int glyphID = 0; glyphID < numGlyphs; ++glyphID) {
    printf("\n%%%%Page: %d %d\n", glyphID + 1, glyphID + 1);
    int fontIndex = 0;
    for (float width = 0.7; width <= 1.3; width += 0.05) {
      for (float weight = 0.5; weight <= 3.1; weight += 0.1) {
	int x = static_cast<int>(50 + (width - 0.7) * 600 + 0.5);
	int y = static_cast<int>(100 + (weight - 0.5) * 200 + 0.5);
	Font* gvarFont = gvarFonts[fontIndex];
	++fontIndex;
	printf("gsave %d %d translate\n", x, y);
	PostScriptPen pen;
	gvarFont->DrawGlyphOutline(glyphID, &pen);
	printf("fill\n");
	printf("grestore\n");
      }
    }
    printf("/Helvetica-Bold 10 selectfont 50 50 moveto (%d ) show\n",
           glyphID + 1);
    printf("/Helvetica 10 selectfont (%s %s) show\n",
           font->GetPostScriptName().c_str(),
           font->GetGlyphName(glyphID).c_str());
    printf("showpage\n");
  }

  for (int i = 0; i < gvarFonts.size(); ++i) {
    delete gvarFonts[i];
  }
  delete font;
}
