#include <QWidget>
#include <QLabel>
#include <QApplication>
#include <random>
#include "masonry.hpp"

class TestWidget:public QWidget{
public:
    TestWidget(){
        srand((unsigned) time(NULL));
        m_layout = new QMasonryFlowLayout();
        m_layout->setHorizontalAdaption(Zoom);
        m_layout->setVerticalExpansion(HeightBalance);
        m_layout->setOverflow(AutoZoom);
        m_layout->setColumnWidth(150);
        setLayout(m_layout);
        for(int index=0;index<20;++index){
            QLabel *label = new QLabel();
            label->setFixedHeight(int(rand()%150+50));
            label->setFixedWidth(150);
            label->setStyleSheet("background-color:green");
            this->m_layout->addWidget(label);
        }
    }
private:
    QMasonryFlowLayout *m_layout;
};

int main(int argc,char** argv){
    QApplication app(argc,argv);
    QWidget *widget = new TestWidget();
    widget->show();
    return QApplication::exec();;
}