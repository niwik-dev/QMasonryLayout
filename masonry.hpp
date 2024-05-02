#include <QLayout>
#include <QWidget>
#include <stdexcept>
#include <algorithm>
#include <QDebug>

enum HorizontalAdaptationStrategy{
    NoAdaption,
    Spacing,
    Zoom,
};

typedef HorizontalAdaptationStrategy HAdapt;

enum VerticalExpansionStrategy{
    HeightBalance,
    OrderInsert,
    RandomInsert
};

typedef VerticalExpansionStrategy VExpand;

enum OverflowStrategy{
    Ignore,
    AutoZoom,
    AutoCrop,
};

typedef OverflowStrategy Overflow;

class QMasonryFlowLayout : public QLayout
{
    Q_OBJECT
    Q_PROPERTY(HAdapt horizontalAdaption READ horizontalAdaption WRITE setHorizontalAdaption)
    Q_PROPERTY(VExpand verticalExpansion READ verticalExpansion WRITE setVerticalExpansion)
    Q_PROPERTY(Overflow overflow READ overflow WRITE setOverflow)
    Q_PROPERTY(int columnCount READ columnCount WRITE setColumnCount)
    Q_PROPERTY(int columnWidth READ columnWidth WRITE setColumnWidth)

    Q_ENUM(HorizontalAdaptationStrategy)
    Q_ENUM(VerticalExpansionStrategy)
    Q_ENUM(OverflowStrategy)
public:
    explicit QMasonryFlowLayout(QWidget *parent = nullptr): QLayout(parent){
        m_horizontal_adaption = Zoom;
        m_vertical_expansion = HeightBalance;
        m_overflow = AutoZoom;

        m_column_width = 200;

        m_horizontal_spacing = 16;
        m_vertical_spacing = 16;

        m_items.clear();
        m_item_ratios.clear();
    }

private:
    HorizontalAdaptationStrategy m_horizontal_adaption = Zoom;
    VerticalExpansionStrategy m_vertical_expansion = HeightBalance;
    OverflowStrategy m_overflow = AutoZoom;

    std::optional<int> m_column_count;
    std::optional<int> m_column_width;

    int m_horizontal_spacing = 0;
    int m_vertical_spacing = 0;

    QList<QLayoutItem*> m_items;
    QList<double> m_item_ratios;
public:
    void setHorizontalAdaption(HorizontalAdaptationStrategy strategy){
        m_horizontal_adaption = strategy;
    }
    HorizontalAdaptationStrategy horizontalAdaption() const{
        return m_horizontal_adaption;
    }

    void setVerticalExpansion(VerticalExpansionStrategy strategy){
        m_vertical_expansion = strategy;
    }
    VerticalExpansionStrategy verticalExpansion() const{
        return m_vertical_expansion;
    }

    void setOverflow(OverflowStrategy strategy){
        m_overflow = strategy;
    }
    OverflowStrategy overflow() const{
        return m_overflow;
    }
    void setColumnCount(int count){
        m_column_count = count;
    }

    int columnCount() const{
        return m_column_count.value_or(0);
    }
    void setColumnWidth(qint64 width){
        m_column_width = width;
    }

    int columnWidth() const{
        return m_column_width.value_or(0);
    }
    void setHorizontalSpacing(int spacing){
        m_horizontal_spacing = spacing;
    }

    int horizontalSpacing() const{
        return m_horizontal_spacing;
    }

    void setVerticalSpacing(int spacing){
        m_vertical_spacing = spacing;
    }
    int verticalSpacing() const{
        return m_vertical_spacing;
    }

    void addItem(QLayoutItem *item) override{
        m_items.append(item);
        QWidget*widget = item->widget();
        if(widget!= nullptr){
            m_item_ratios.append(double(widget->height())/widget->width());
        }
    }

    QSize sizeHint() const override{
        return QLayout::minimumSize();
    }

    void setGeometry(const QRect &rect) override{
        QLayout::setGeometry(rect);
        doLayout(rect);
    }

    QLayoutItem * itemAt(int index) const override{
        if(index>=0 && index<m_items.length()){
            return nullptr;
        }
        return m_items.at(index);
    }

    QLayoutItem *takeAt(int index){
        if(index>=0 && index<m_items.length()){
            return nullptr;
        }
        return m_items.takeAt(index);
    }

    int count() const override{
        return m_items.length();
    }
private:
    void calculateColumnCount(const QRect& rect){
        QMargins margin = contentsMargins();
        int space_x = m_horizontal_spacing;

        int column_count = std::max(1,rect.width()-margin.left()-margin.right()+space_x)/(m_column_width.value_or(0)+space_x);
        m_column_count = column_count;
    }

    void handleOverflow(QLayoutItem*&item){
        QWidget* item_widget = item->widget();
        int item_height = item_widget->sizeHint().height();
        int item_width = item_widget->sizeHint().width();

        if(item_widget->width()!=columnWidth()){
            switch (m_overflow)
            {
                case AutoZoom: {
                    int column_height = item_height * columnWidth() / item_width;
                    item_widget->setFixedSize(columnWidth(), column_height);
                    break;
                }
                case AutoCrop:{
                    item_widget->setFixedWidth(columnWidth());
                    break;
                }
                case Ignore:{
                    break;
                }
                default:{
                    throw std::runtime_error("Invalid overflow strategy");
                }
            }
        }
    }

    int handleColumnSelection(int item_index,const QList<double>& column_total_heights){
        int target_column_index = 0;
        switch (m_vertical_expansion) {
            case HeightBalance:{
                int min_column_total_height = column_total_heights[0];
                for(int column_index=0;column_index<m_column_count.value_or(0);++column_index){
                    int column_total_height = column_total_heights[column_index];
                    if(column_total_height<min_column_total_height){
                        min_column_total_height = column_total_height;
                        target_column_index = column_index;
                    }
                }
                break;
            }
            case OrderInsert:{
                target_column_index = item_index%m_column_count.value_or(0);
                break;
            }
            case RandomInsert:{
                target_column_index = int(rand())%m_column_count.value_or(0);
            }
            default:{
                throw std::runtime_error("Invalid vertical expansion strategy");
            }
        }
        return target_column_index;
    }

    void handlePosition(const QRect&rect,
                        int target_column_index,QList<double>& column_total_heights,
                        QLayoutItem*&item,double item_ratio,
                        QRect& out_rect){
        QMargins margin = contentsMargins();
        int space_x = m_horizontal_spacing;
        int space_y = m_vertical_spacing;
        int item_width = item->widget()->sizeHint().width();
        int item_height = item->widget()->sizeHint().height();
        QWidget*item_widget = item->widget();

        auto getItemTopLeft = [&](double column_width,int& out_x,int&out_y){
            out_x = margin.left() + column_width*(target_column_index+0.5)+space_x*target_column_index - item_width/2;
            out_y = margin.top() + column_total_heights[target_column_index];
        };

        auto getRealColumnWidth = [&](int column_index){
            return (rect.width()-margin.left()-margin.right()-space_x*(m_column_count.value_or(0)-1))/m_column_count.value_or(0);
        };

        int x=0,y=0;
        switch (m_horizontal_adaption) {
            case NoAdaption:{
                getItemTopLeft(columnWidth(),x,y);
                column_total_heights[target_column_index] += item_height+space_y;
                break;
            }
            case Spacing:{
                int real_column_width = getRealColumnWidth(target_column_index);
                getItemTopLeft(real_column_width,x,y);
                column_total_heights[target_column_index] += item_height+space_y;
                break;
            }
            case Zoom:{
                double real_column_width = getRealColumnWidth(target_column_index);
                getItemTopLeft(real_column_width,x,y);
                double column_height = real_column_width*item_ratio;
                qDebug()<<column_height<<Qt::endl;
                item_widget->setFixedSize(QSize(real_column_width, column_height));
                column_total_heights[target_column_index] += column_height+space_y;
                break;
            }
            default:{
                throw std::runtime_error("Invalid horizontal adaptation strategy");
            }
        }
        out_rect.setRect(x,y,item_width,item_height);
    }

    QSize doLayout(const QRect& rect){
        calculateColumnCount(rect);
        QList<double> column_total_heights(m_column_count.value_or(0),0);
        QRect position;

        for(int item_index = 0;item_index<m_items.size();++item_index){
            QLayoutItem*item = m_items[item_index];
            handleOverflow(item);

            double item_ratio = m_item_ratios[item_index];
            int target_column_index = handleColumnSelection(item_index,column_total_heights);
            handlePosition(rect,
                           target_column_index,column_total_heights,
                           item,item_ratio,
                           position);

            item->setGeometry(position);
        }
        return QSize(rect.width(),*std::max(column_total_heights.begin(),column_total_heights.end()));
    }
};