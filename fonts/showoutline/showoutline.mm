#include <stdio.h>
#include <memory>
#include <string>

#include "ApplicationServices/ApplicationServices.h"
#include "CoreGraphics/CoreGraphics.h"
#include "CoreText/CoreText.h"
#include "Foundation/Foundation.h"

class Font {
 public:
  static Font* FromFile(const char* path);
  ~Font();

  std::string GetPostScriptName() const;
  std::string GetGlyphPath(const std::string& glyph) const;

 private:
  Font(CGDataProviderRef provider);

  CGDataProviderRef provider_;
  CGFontRef core_graphics_font_;
  CTFontRef font_;
};

Font* Font::FromFile(const char* path) {
  CGDataProviderRef provider = CGDataProviderCreateWithFilename(path);
  if (provider == NULL) {
    return NULL;
  }

  Font* result = new Font(provider);
  return result;
}

Font::Font(CGDataProviderRef provider)
  : provider_(provider),
    core_graphics_font_(CGFontCreateWithDataProvider(provider)),
    font_(CTFontCreateWithGraphicsFont(core_graphics_font_, 12, NULL, NULL)) {
}

std::string Font::GetPostScriptName() const {
  if (font_ == NULL) {
    return "";
  }

  std::string result;
  const NSString* nsname =
      reinterpret_cast<const NSString*>(CTFontCopyPostScriptName(font_));
  result.assign([nsname UTF8String]);
  [nsname release];
  return result;
}

class PathRecorder {
 public:
  void Record(CGPathRef path);
  const std::string& value() const { return value_; }

 private:
  static void Visit_(void* data, const CGPathElement* element);
  std::string value_;
};

void PathRecorder::Record(CGPathRef path) {
  if (path != NULL) {
    CGPathApply(path, reinterpret_cast<void*>(this), &PathRecorder::Visit_);
  }
}

void PathRecorder::Visit_(void* data, const CGPathElement* element) {
  PathRecorder* recorder = reinterpret_cast<PathRecorder*>(data);
  
  char buf[100];
  switch (element->type) {
  case kCGPathElementMoveToPoint:
    snprintf(buf, sizeof(buf), "%0.5f %0.5f moveto\n",
             element->points[0].x, element->points[0].y);
    break;

  case kCGPathElementAddLineToPoint:
    snprintf(buf, sizeof(buf), "%0.5f %0.5f lineto\n",
             element->points[0].x, element->points[0].y);
    break;

  case kCGPathElementAddQuadCurveToPoint:
    snprintf(buf, sizeof(buf), "%0.5f %0.5f %0.5f %0.5f quadto\n",
             element->points[0].x, element->points[0].y,
             element->points[1].x, element->points[1].y);
    break;

  case kCGPathElementAddCurveToPoint:
    snprintf(buf, sizeof(buf), "%0.5f %0.5f %0.5f %0.5f %0.5f %0.5f curveto\n",
             element->points[0].x, element->points[0].y,
             element->points[1].x, element->points[1].y,
             element->points[2].x, element->points[2].y);
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

std::string Font::GetGlyphPath(const std::string& glyph) const {
  if (font_ == NULL) {
    return "";
  }

  NSString* glyphName = [NSString stringWithUTF8String:glyph.c_str()];
  CGGlyph glyphNumber =
      CTFontGetGlyphWithName(font_, reinterpret_cast<CFStringRef>(glyphName));
  CGPathRef path = CTFontCreatePathForGlyph(font_, glyphNumber, NULL);
  [glyphName release];

  PathRecorder recorder;
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

  if (provider_ != NULL) {
    CGDataProviderRelease(provider_);
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
    std::string path = font->GetGlyphPath([glyph UTF8String]);
    if (path.find("quadto") != std::string::npos) {
      printf("/quadto { /y exch def /x exch def x y x y curveto} def\n");
    }
    printf("newpath\n%sfill\n", path.c_str());
    delete font;
  }
  [pool release];
  return 0;
}
