#include <stdio.h>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "ApplicationServices/ApplicationServices.h"
#include "CoreGraphics/CoreGraphics.h"
#include "CoreText/CoreText.h"
#include "Foundation/Foundation.h"

typedef std::vector<std::pair<float, float> > PointVector;

class Font {
 public:
  static Font* FromFile(const char* path);
  ~Font();

  typedef std::map<std::string, float> VariationMap;
  void GetVariations(VariationMap* variation) const;
  Font* MakeVariation(const VariationMap& variation) const;

  std::string GetPostScriptName() const;
  std::string GetGlyphPath(const std::string& glyph,
                           PointVector* points) const;

 private:
  Font(CGFontRef core_graphics_font);

  CGDataProviderRef provider_;
  CGFontRef core_graphics_font_;
  CTFontRef font_;
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

Font::Font(CGFontRef font)
  : core_graphics_font_(font),
    font_(CTFontCreateWithGraphicsFont(core_graphics_font_, 500, NULL, NULL)) {
  CGFontRetain(font);
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
      CGFontCreateCopyWithVariations(core_graphics_font_,
                                     reinterpret_cast<CFDictionaryRef>(dict));
  return new Font(gvarFont);
}

void Font::GetVariations(Font::VariationMap* gvar) const {
  gvar->clear();
  CFArrayRef axes = CGFontCopyVariationAxes(core_graphics_font_);
  const CFIndex numAxes = CFArrayGetCount(axes);
  //NSLog(@"All my array list: %@", reinterpret_cast<const NSArray*>(axes));
  for (CFIndex axis = 0; axis < numAxes; ++axis) {
    CFDictionaryRef dict =
        reinterpret_cast<CFDictionaryRef>(CFArrayGetValueAtIndex(axes, axis));
  }
  CFRelease(axes);

  (*gvar)["foo"] = 3.141;
  (*gvar)["bar"] = 7;
}

std::string Font::GetPostScriptName() const {
  if (font_ == NULL) {
    return "";
  }

  std::string result;
  const NSString* nsname =
      reinterpret_cast<const NSString*>(CGFontCopyPostScriptName(core_graphics_font_));
  result.assign([nsname UTF8String]);
  [nsname release];
  return result;
}

class PathRecorder {
 public:
  PathRecorder(PointVector* points) : points_(points) {}
  void Record(CGPathRef path);
  const std::string& value() const { return value_; }

 private:
  static void Visit_(void* data, const CGPathElement* element);
  std::string value_;
  PointVector* points_;
};

void PathRecorder::Record(CGPathRef path) {
  if (path != NULL) {
    CGPathApply(path, reinterpret_cast<void*>(this), &PathRecorder::Visit_);
  }
}

void PathRecorder::Visit_(void* data, const CGPathElement* element) {
  PathRecorder* recorder = reinterpret_cast<PathRecorder*>(data);
  
  char buf[100];
  float x, y, ax, ay, bx, by;
  switch (element->type) {
  case kCGPathElementMoveToPoint:
    x = element->points[0].x;
    y = element->points[0].y;
    recorder->points_->push_back(std::make_pair(x, y));
    snprintf(buf, sizeof(buf), "%0.5f %0.5f moveto\n", x, y);
    break;

  case kCGPathElementAddLineToPoint:
    x = element->points[0].x;
    y = element->points[0].y;
    recorder->points_->push_back(std::make_pair(x, y));
    snprintf(buf, sizeof(buf), "%0.5f %0.5f lineto\n", x, y);
    break;

  case kCGPathElementAddQuadCurveToPoint:
    ax = element->points[0].x;
    ay = element->points[0].y;
    x = element->points[1].x;
    y = element->points[1].y;
    // recorder->points_->push_back(std::make_pair(ax, ay));
    recorder->points_->push_back(std::make_pair(x, y));
    snprintf(buf, sizeof(buf), "%0.5f %0.5f %0.5f %0.5f quadto\n",
             ax, ay, x, y);
    break;

  case kCGPathElementAddCurveToPoint:
    ax = element->points[0].x;
    ay = element->points[0].y;
    bx = element->points[1].x;
    by = element->points[1].y;
    x = element->points[2].x;
    y = element->points[2].y;
    // recorder->points_->push_back(std::make_pair(ax, ay));
    // recorder->points_->push_back(std::make_pair(bx, by));
    recorder->points_->push_back(std::make_pair(x, y));
    snprintf(buf, sizeof(buf), "%0.5f %0.5f %0.5f %0.5f %0.5f %0.5f curveto\n",
             ax, ay, bx, by, x, y);
    break;

  case kCGPathElementCloseSubpath:
    snprintf(buf, sizeof(buf), "closepath\n");
    break;

  default:
    snprintf(buf, sizeof(buf), "???\n");
    break;
  }
  recorder->value_.append(buf);
}

std::string Font::GetGlyphPath(const std::string& glyph,
                               PointVector* points) const {
  if (font_ == NULL) {
    return "";
  }

  NSString* glyphName = [NSString stringWithUTF8String:glyph.c_str()];
  CGGlyph glyphNumber =
      CTFontGetGlyphWithName(font_, reinterpret_cast<CFStringRef>(glyphName));
  CGPathRef path = CTFontCreatePathForGlyph(font_, glyphNumber, NULL);
  [glyphName release];

  PathRecorder recorder(points);
  recorder.Record(path);
  CGPathRelease(path);
  return recorder.value();
}

Font::~Font() {
  if (font_ != NULL) {
    CFRelease(font_);
  }

  if (core_graphics_font_ != NULL) {
    CGFontRelease(core_graphics_font_);
  }
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
  NSString* glyph = [args stringForKey:@"glyph"];
  {
    Font* font = Font::FromFile([fontPath UTF8String]);
    if (font == NULL) {
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
    int page = 1;
    for (float width = 0.7; width <= 1.3; width += 0.1) {
      for (float weight = 0.5; weight <= 3.1; weight += 0.1) {
        printf("\n%%%%Page: %d %d\n", page, page);
	page += 1;
	Font::VariationMap variations;
	variations["Width"] = width;
	variations["Weight"] = weight;
	Font* gvarFont = font->MakeVariation(variations);
	std::string psname = gvarFont->GetPostScriptName();	
	printf("/Helvetica-Bold 10 selectfont 10 10 moveto (%s %s ) show\n",
               psname.c_str(), [glyph UTF8String]);
	printf("/Helvetica 10 selectfont (width: %.1f weight: %.1f) show\n",
               width, weight);

	PointVector points;
	std::string path = gvarFont->GetGlyphPath([glyph UTF8String], &points);
	printf("100 100 translate\n");
        printf("newpath\n%s", path.c_str());
	printf("gsave 0.8 setgray fill grestore stroke\n\n");
	printf("0.9 0.4 0.1 setrgbcolor\n");
	printf("/Helvetica 6 selectfont\n");
	for (int i = 0; i < points.size(); ++i) {
	  float x = points[i].first;
	  float y = points[i].second;
	  printf("newpath %.5f %.5f 2 0 360 arc fill\n", x, y);
	  printf("%.5f %.5f moveto (%d) show\n", x + 3, y - 1.5, i + 1);
	}
	printf("showpage\n");
	delete gvarFont;
      }
    }
    printf("%%%%EOF\n");
    delete font;
  }
  [pool release];
  return 0;
}
