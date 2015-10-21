#include <QtGui>
#include <QApplication>
#include <QCommandLineParser>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QGraphicsWidget>
#include <QHBoxLayout>
#include <QLabel>
#include <QObject>
#include <QObject>
#include <QPushButton>
#include <QSlider>
#include <QVBoxLayout>
#include <QWidget>
#include <hb.h>
#include <hb-ft.h>
#include <ftmm.h>
#include <iostream>
#include <map>
#include <memory>
#include <string>


FT_Library freeTypeLibrary;

typedef std::map<std::string, float> AxisVariations;

class TextWidget : public QGraphicsWidget {
public:
  TextWidget() : QGraphicsWidget(), ftFont_(NULL), hbFont_(NULL) {
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
  
  void paint(QPainter* painter, const QStyleOptionGraphicsItem*, QWidget* = 0) Q_DECL_OVERRIDE {
    qreal marginSize = 10.0;
    qreal fontScale = 64.0;
    int fontSize = 50;

    //painter->fillRect(boundingRect(), Qt::blue);
    //std::cout << "text: \"" << text_ << "\"; font: " << hbFont_ << "\n";
    recreateHarfbuzzFont();
    if (!hbFont_) return;

    hb_buffer_t *hbBuffer = hb_buffer_create();
    hb_buffer_add_utf8(hbBuffer, text_.c_str(), -1, 0, -1);
    hb_buffer_set_language(hbBuffer, language_);
    hb_buffer_set_direction(hbBuffer, HB_DIRECTION_LTR);

    hb_shape(hbFont_, hbBuffer, NULL, 0);
    int nGlyphs = hb_buffer_get_length(hbBuffer);
    
    hb_glyph_info_t *hbGlyphs = hb_buffer_get_glyph_infos(hbBuffer, NULL);
    hb_glyph_position_t *hbPositions =
        hb_buffer_get_glyph_positions(hbBuffer, NULL);

    // map shaped glyph indices and position for Qt's glyph run
    QVector<quint32> glyphIndexes(nGlyphs);
    QVector<QPointF> glyphPositions(nGlyphs);

    // std::cout << "text: \"" << text_ << "\"; numGlyphs: " << nGlyphs << "\n";
    
    qreal x = 0.0, y = 0.0;
    for (int i = 0; i < nGlyphs; i++, hbGlyphs++, hbPositions++) {
      glyphIndexes[i] = hbGlyphs->codepoint;
      glyphPositions[i] = QPointF(x + hbPositions->x_offset, y - hbPositions->y_offset) / fontScale;
      x += hbPositions->x_advance;
      y -= hbPositions->y_advance;
      // std::cout << "glyph " << i << ": codepoint=" << hbGlyphs->codepoint
      // << ", x=" << x << ", y=" << y << "\n";
    }

    QRawFont rawFont = QRawFont(QString("/home/sascha/src/fonttools/tmp/Skia-Regular.ttf"), fontSize);
    QGlyphRun glyphRun = QGlyphRun();

    glyphRun.setRawFont(rawFont);
    glyphRun.setGlyphIndexes(glyphIndexes);
    glyphRun.setPositions(glyphPositions);

    painter->drawGlyphRun(QPointF(marginSize, rawFont.ascent() + marginSize),
			  glyphRun);
    hb_buffer_destroy(hbBuffer);
  }

private:
  void recreateHarfbuzzFont() {
    if (hbFont_) {
      hb_font_destroy(hbFont_);
      hbFont_ = NULL;
    }

    std::cout << "*** wdth: " << variations_["wdth"]
	      << ", wght: " << variations_["wght"] << "\n";

    FT_Fixed coord[2];
    coord[0] = static_cast<FT_Fixed>(variations_["wght"] * 65536);
    coord[1] = static_cast<FT_Fixed>(variations_["wdth"] * 65536);
    std::cout << "**A wdth: " << coord[0]
	      << ", wght: " << coord[1] << "\n";
    int status = static_cast<int>(
        FT_Set_Var_Design_Coordinates(ftFont_, 2, coord));
    if (status) std::cout << "SetCoords: " << status << "\n";
    status = static_cast<int>(FT_Load_Glyph(ftFont_, 123, FT_LOAD_DEFAULT));
    if (!status) std::cout << "glyph.metrics.width: "
			   << ftFont_->glyph->metrics.width << "\n";
		   
    //std::cout << "numGlyphs=" << ftFont_->num_glyphs << "\n";
    hbFont_ = hb_ft_font_create(ftFont_, NULL);
  }
  
  std::string text_;
  FT_Face ftFont_;
  hb_font_t* hbFont_;
  hb_language_t language_;
  AxisVariations variations_;
};


class ATMWindow {
public:
  ATMWindow()
    : weightSlider_(new QSlider(Qt::Horizontal)),
      widthSlider_(new QSlider(Qt::Horizontal)),
      widget_(new QWidget()) {
    QGraphicsScene* textScene = new QGraphicsScene();
    textWidget_ = new TextWidget();
    textWidget_->setPreferredSize(200, 200);
    QGraphicsView* textView = new QGraphicsView();
    textScene->addItem(textWidget_);
    textView->setScene(textScene);

    QGridLayout* gridLayout = new QGridLayout();
    
    QLabel* weightLabel = new QLabel("Weight:");
    weightSlider_->setMinimum(48);
    weightSlider_->setMaximum(320);
    weightSlider_->setValue(100);
    weightLabel->setBuddy(weightSlider_);
    QObject::connect(weightSlider_, &QSlider::valueChanged,
		     [=](int) {RedrawText();});

    QLabel* widthLabel = new QLabel("Width:");
    widthSlider_->setMinimumWidth(300);
    widthSlider_->setMinimum(62);
    widthSlider_->setMaximum(129);
    widthSlider_->setValue(100);
    widthLabel->setBuddy(widthSlider_);
    QObject::connect(widthSlider_, &QSlider::valueChanged,
		     [=](int) {RedrawText();});

    // addWidget(*Widget, row, column, rowspan, colspan)
    gridLayout->addWidget(textView, 0, 0, 1, 2);
    gridLayout->addWidget(weightLabel, 1, 0, 1, 1);
    gridLayout->addWidget(weightSlider_, 1, 1, 1, 1);
    gridLayout->addWidget(widthLabel, 2, 0, 1, 1);
    gridLayout->addWidget(widthSlider_, 2, 1, 1, 1);

    widget_->setLayout(gridLayout);
    widget_->setWindowTitle("Skia");
    widget_->show();
  }

  void setFont(const std::string& path) {
    FT_New_Face(freeTypeLibrary, path.c_str(), 0, &font_);
    FT_Set_Pixel_Sizes(font_, 0, 48);
    textWidget_->setFont(font_);
  }

  void setText(const std::string& text) {
    textWidget_->setText(text);
  }

private:
  void RedrawText() {
    AxisVariations v;
    v["wdth"] = widthSlider_->value() * .01f;
    v["wght"] = weightSlider_->value() * .01f;
    textWidget_->setVariations(v);
  }

  FT_Face font_;
  hb_font_t* harfbuzzFont_;

  TextWidget* textWidget_;
  QSlider* weightSlider_;
  QSlider* widthSlider_;
  std::unique_ptr<QWidget> widget_;
};

int main(int argc, char* argv[]) {
  QApplication app(argc, argv);
  app.setApplicationName("atm");

  QCommandLineParser cmd;
  cmd.addHelpOption();
  QCommandLineOption textOption(
      QStringList() << "t" << "text",
      QCoreApplication::translate("main", "Text to display."),
      QCoreApplication::translate("main", "Text to display."));
  cmd.addOption(textOption);

  cmd.addPositionalArgument("source", QCoreApplication::translate("font", "Font file to view."));
  cmd.setApplicationDescription("Awesome Type Morpher");
  cmd.process(app);
  const QStringList args = cmd.positionalArguments();
  if (args.isEmpty()) {
    std::cerr << "Usage: atm --text Foobar path/to/font.otf\n";
    return 1;
  }

  std::cout << "****************** " << args.at(0).toUtf8().constData()
	    << "; " << cmd.value(textOption).toUtf8().constData() << "\n";

  FT_Init_FreeType(&freeTypeLibrary);
  ATMWindow window;
  window.setFont(args.at(0).toUtf8().constData());
  window.setText(cmd.value(textOption).toUtf8().constData());

  int status = app.exec();
  FT_Done_FreeType(freeTypeLibrary);
  return status;
}
