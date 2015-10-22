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
static const int FONT_SIZE = 80;

class TextWidget : public QGraphicsWidget {
public:
  TextWidget()
    : QGraphicsWidget(), ftFont_(NULL), hbFont_(NULL), shaping_active_(false) {
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

  void setVariations(const AxisVariations& variations) {
    variations_ = variations;
    update();
  }

  void setShapingActive(bool active) {
    shaping_active_ = active;
  }

  void paint(QPainter* painter, const QStyleOptionGraphicsItem*, QWidget* = 0) Q_DECL_OVERRIDE {
    recreateHarfbuzzFont();
    if (!hbFont_) return;

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
        std::cout << "glyph='" << glyphname << "' cluster=" << cluster
		  << " position=" << x_position << ", " << y_position << "\n";
      }

      FT_Glyph glyph;
      if (FT_Load_Glyph(ftFont_, glyphs[i].codepoint, FT_LOAD_DEFAULT)) continue;
      if (FT_Get_Glyph(ftFont_->glyph, &glyph)) continue;
      if (glyph->format != FT_GLYPH_FORMAT_BITMAP) {
	if (FT_Glyph_To_Bitmap(&glyph, FT_RENDER_MODE_NORMAL, 0, false)) continue;
      }

      FT_BitmapGlyph rendered = reinterpret_cast<FT_BitmapGlyph>(glyph);
      FT_Bitmap_Convert(freeTypeLibrary, &rendered->bitmap, &converted, 4);
      QImage glyphImage(converted.buffer, converted.width, converted.rows,
			converted.pitch, QImage::QImage::Format_Indexed8);
      glyphImage.setColorTable(palette);
      painter->drawImage(QPoint(current_x + rendered->left,
				current_y + FONT_SIZE - rendered->top),
			 glyphImage);

      if (shaping_active_) {
	current_x += pos[i].x_advance / 64.;
	current_y += pos[i].y_advance / 64.;
      } else {
	current_x += glyph->advance.x >> 16;
	current_y += glyph->advance.y >> 16;
      }

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
    int status = static_cast<int>(
        FT_Set_Var_Design_Coordinates(ftFont_, 2, coord));
    if (status) std::cout << "SetCoords: " << status << "\n";
    status = static_cast<int>(FT_Load_Glyph(ftFont_, 123, FT_LOAD_DEFAULT));
    if (status) std::cout << "glyph.metrics.width: "
			  << ftFont_->glyph->metrics.width << "\n";
    hbFont_ = hb_ft_font_create(ftFont_, NULL);
  }
  
  std::string text_;
  FT_Face ftFont_;
  hb_font_t* hbFont_;
  hb_language_t language_;
  AxisVariations variations_;
  bool shaping_active_;
};


class MainWindow {
public:
  MainWindow()
    : textWidget_(new TextWidget()),
      shapingCheckBox_(new QCheckBox("Shaping")),
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
    QGraphicsScene* textScene = new QGraphicsScene();
    QGraphicsView* textView = new QGraphicsView();
    textScene->addItem(textWidget_);
    textView->setScene(textScene);

    QGridLayout* gridLayout = new QGridLayout();
    
    QLabel* weightLabel = new QLabel("Weight:");
    QSlider* weightSlider = new QSlider(Qt::Horizontal);
    sliders_.push_back(weightSlider);
    weightSlider->setMinimum(48);
    weightSlider->setMaximum(320);
    weightSlider->setValue(100);
    weightLabel->setBuddy(weightSlider);
    QObject::connect(weightSlider, &QSlider::valueChanged,
		     [=](int) {redrawText();});

    QLabel* widthLabel = new QLabel("Width:");
    QSlider* widthSlider = new QSlider(Qt::Horizontal);
    sliders_.push_back(widthSlider);
    widthSlider->setMinimumWidth(300);
    widthSlider->setMinimum(62);
    widthSlider->setMaximum(129);
    widthSlider->setValue(100);
    widthLabel->setBuddy(widthSlider);
    QObject::connect(widthSlider, &QSlider::valueChanged,
		     [=](int) {redrawText();});

    QObject::connect(shapingCheckBox_, &QCheckBox::stateChanged,
		     [=](int) {redrawText();});

    // addWidget(*Widget, row, column, rowspan, colspan)
    gridLayout->addWidget(textView, 0, 0, 1, 2);
    gridLayout->addWidget(weightLabel, 1, 0, 1, 1);
    gridLayout->addWidget(weightSlider, 1, 1, 1, 1);
    gridLayout->addWidget(widthLabel, 2, 0, 1, 1);
    gridLayout->addWidget(widthSlider, 2, 1, 1, 1);
    gridLayout->addWidget(shapingCheckBox_, sliders_.size() + 1, 1, 1, 1);

    widget_->setLayout(gridLayout);
    widget_->setWindowTitle("Morphable Type");

    textWidget_->setPreferredSize(800, 200);

    redrawText();
    widget_->show();
  }

private:
  void redrawText() {
    AxisVariations v;
    v.push_back(static_cast<FT_Fixed>(sliders_[0]->value() * .01f * 65536));
    v.push_back(static_cast<FT_Fixed>(sliders_[1]->value() * .01f * 65536));
    textWidget_->setVariations(v);
    textWidget_->setShapingActive(shapingCheckBox_->isChecked());
  }

  FT_Face font_;
  hb_font_t* harfbuzzFont_;

  TextWidget* textWidget_;
  std::vector<QSlider*> sliders_;
  QCheckBox* shapingCheckBox_;
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
