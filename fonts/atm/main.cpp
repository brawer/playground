#include <QApplication>
#include <QCheckBox>
#include <QCommandLineParser>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QGraphicsWidget>
#include <QHBoxLayout>
#include <QImage>
#include <QLabel>
#include <QObject>
#include <QObject>
#include <QPushButton>
#include <QSlider>
#include <QVBoxLayout>
#include <QWidget>
#include <QtGui>

#include <hb.h>
#include <hb-ft.h>

#include <ftbitmap.h>
#include <ftglyph.h>
#include <ftimage.h>
#include <ftmm.h>

#include <iostream>
#include <map>
#include <memory>
#include <string>


FT_Library freeTypeLibrary;

typedef std::vector<FT_Fixed> AxisVariations;
static const int FONT_SIZE = 384;

class TextWidget : public QGraphicsWidget {
public:
  TextWidget()
    : QGraphicsWidget(), ftFont_(NULL), hbFont_(NULL) {
    setLanguage("und");
  }

  void setText(const std::string& text) {
    text_ = text;
  }

  void setFont(FT_Face ftFont) {
    ftFont_ = ftFont;
  }

  void setLanguage(const std::string& lang) {
    language_ = hb_language_from_string(lang.c_str(), lang.size());
  }

  void setVariations(const AxisVariations& variations, unsigned int num_axes) {
    variations_ = variations;
    num_axes_ = num_axes;
    update();
  }

  void paint(QPainter* painter, const QStyleOptionGraphicsItem*, QWidget* = 0) Q_DECL_OVERRIDE {
    recreateHarfbuzzFont();
    if (!hbFont_) {
      return;
    }

    hb_buffer_t *hbBuffer = hb_buffer_create();
    hb_buffer_add_utf8(hbBuffer, text_.c_str(), -1, 0, -1);
    hb_buffer_guess_segment_properties(hbBuffer);
    //hb_buffer_set_language(hbBuffer, language_);
    //hb_buffer_set_direction(hbBuffer, HB_DIRECTION_LTR);

    hb_shape(hbFont_, hbBuffer, NULL, 0);
    int numGlyphs = hb_buffer_get_length(hbBuffer);
    
    hb_glyph_info_t* glyphs = hb_buffer_get_glyph_infos(hbBuffer, NULL);
    hb_glyph_position_t* pos = hb_buffer_get_glyph_positions(hbBuffer, NULL);

    QVector<QRgb> palette;
    for (int i = 0; i < 256; ++i) {
      palette.append(qRgba(255 - i, 255 - i, 255 - i, i));
    }
    
    FT_Bitmap converted;
    FT_Bitmap_New(&converted);

    double current_x = 0;
    double current_y = 0;
    for (int i = 0; i < numGlyphs; i++) {
      hb_codepoint_t gid   = glyphs[i].codepoint;
      unsigned int cluster = glyphs[i].cluster;
      double x_position = current_x + pos[i].x_offset / 64.;
      double y_position = current_y + pos[i].y_offset / 64.;

      char glyphname[32];
      hb_font_get_glyph_name(hbFont_, gid, glyphname, sizeof(glyphname));
      if (false) {
        std::cout << "glyph='" << glyphname
		  << "' gid=" << gid
		  << " cluster=" << cluster
		  << " position=" << x_position << ", " << y_position << "\n";
      }

      FT_Glyph glyph;
      if (FT_Load_Glyph(ftFont_, glyphs[i].codepoint, FT_LOAD_DEFAULT|FT_LOAD_NO_HINTING)) {
	continue;
      }
      
      if (FT_Get_Glyph(ftFont_->glyph, &glyph)) {
	continue;
      }
      
      if (glyph->format != FT_GLYPH_FORMAT_BITMAP) {
	if (FT_Glyph_To_Bitmap(&glyph, FT_RENDER_MODE_NORMAL, 0, false)) {
	  continue;
	}
      }

      FT_BitmapGlyph rendered = reinterpret_cast<FT_BitmapGlyph>(glyph);
      FT_Bitmap_Convert(freeTypeLibrary, &rendered->bitmap, &converted, 4);
      QImage glyphImage(converted.buffer, converted.width, converted.rows,
			converted.pitch, QImage::QImage::Format_Indexed8);
      glyphImage.setColorTable(palette);
      painter->drawImage(QPoint(current_x + rendered->left,
				current_y + FONT_SIZE - rendered->top),
			 glyphImage);

      current_x += pos[i].x_advance / 64.;
      current_y += pos[i].y_advance / 64.;

      FT_Done_Glyph(glyph);
    }

    FT_Bitmap_Done(freeTypeLibrary, &converted);
    hb_buffer_destroy(hbBuffer);
  }

private:
  void recreateHarfbuzzFont() {
    if (hbFont_) {
      hb_font_destroy(hbFont_);
      hbFont_ = NULL;
    }

    FT_Fixed* coord = &variations_[0];
    if (num_axes_) {
      int status = static_cast<int>(
          FT_Set_Var_Design_Coordinates(ftFont_, num_axes_, coord));
      if (status) std::cerr << "SetCoords: " << status << "\n";
    }
    hbFont_ = hb_ft_font_create(ftFont_, NULL);
  }
  
  std::string text_;
  FT_Face ftFont_;
  hb_font_t* hbFont_;
  hb_language_t language_;
  AxisVariations variations_;
  unsigned int num_axes_;
};


class MainWindow {
public:
  MainWindow()
    : textWidget_(new TextWidget()),
      widget_(new QWidget()) {
  }

  void setFont(const std::string& path) {
    FT_New_Face(freeTypeLibrary, path.c_str(), 0, &font_);
    FT_Set_Char_Size(font_, FONT_SIZE << 6, FONT_SIZE << 6, 0, 0);
    textWidget_->setFont(font_);
  }

  void setText(const std::string& text) {
    textWidget_->setText(text);
  }

  void show() {
    if (!font_) {
      std::cerr << "never called setFont()\n";
      return;
    }

    QGraphicsScene* textScene = new QGraphicsScene();
    QGraphicsView* textView = new QGraphicsView();
    textScene->addItem(textWidget_);
    textView->setScene(textScene);

    QGridLayout* gridLayout = new QGridLayout();
    FT_MM_Var* mmvar = NULL;
    if (!FT_Get_MM_Var(font_, &mmvar) && mmvar) {
      for (unsigned int i = 0; i < mmvar->num_axis; ++i) {
	const FT_Var_Axis& axis = mmvar->axis[i];
	QLabel* label = new QLabel(QString("%1:").arg(axis.name));
	QSlider* slider = new QSlider(Qt::Horizontal);
	sliders_.push_back(slider);
	slider->setMinimum(axis.minimum);
	slider->setMaximum(axis.maximum);
	slider->setValue(axis.def);
	gridLayout->addWidget(label, i + 1, 0, 1, 1);
	gridLayout->addWidget(slider, i + 1, 1, 1, 1);
	QObject::connect(slider, &QSlider::valueChanged,
			 [=](int) {redrawText();});
	label->setBuddy(slider);
      }
      free(mmvar);
    }

    textWidget_->setPreferredSize(1920, 1000);

    // addWidget(*Widget, row, column, rowspan, colspan)
    gridLayout->addWidget(textView, 0, 0, 1, 2);

    widget_->setLayout(gridLayout);
    widget_->setWindowTitle("Morphable Type");

    redrawText();
    widget_->show();
  }

private:
  void redrawText() {
    AxisVariations v;
    for (const auto slider : sliders_) {
      v.push_back(static_cast<FT_Fixed>(round (slider->value())));
    }
    textWidget_->setVariations(v, v.size());
  }

  FT_Face font_;
  hb_font_t* harfbuzzFont_;

  TextWidget* textWidget_;
  std::vector<QSlider*> sliders_;
  std::unique_ptr<QWidget> widget_;
};

int main(int argc, char* argv[]) {
  QApplication app(argc, argv);
  app.setApplicationName("Morphable Type");

  QCommandLineParser cmd;
  cmd.addHelpOption();
  QCommandLineOption textOption(
      QStringList() << "t" << "text",
      QCoreApplication::translate("main", "Text to display."),
      QCoreApplication::translate("main", "Text to display."));
  cmd.addOption(textOption);

  cmd.addPositionalArgument(
      "source",
      QCoreApplication::translate("font", "Font file to view."));
  cmd.setApplicationDescription("Morphable Type");
  cmd.process(app);
  const QStringList args = cmd.positionalArguments();
  if (args.isEmpty()) {
    std::cerr << "Usage: morphable_type --text Foobar path/to/font.otf\n";
    return 1;
  }

  FT_Init_FreeType(&freeTypeLibrary);
  MainWindow window;
  window.setFont(args.at(0).toUtf8().constData());
  window.setText(cmd.value(textOption).toUtf8().constData());
  window.show();

  int status = app.exec();
  FT_Done_FreeType(freeTypeLibrary);
  return status;
}
