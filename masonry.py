import enum
import random
from enum import Enum, unique
from typing import Optional

from qtpy.QtCore import Property, QSize, QRect, QMargins
from qtpy.QtWidgets import QLayout, QLayoutItem, QWidget


@unique
class HorizontalAdaptationStrategy(Enum):
    """
    The strategy adopted when the spacing and the width of horizontal sub-items cannot fill the layout width.
    """

    NoAdaption = enum.auto()
    Spacing = enum.auto()
    AutoZoom = enum.auto()


HAdapt = HorizontalAdaptationStrategy


@unique
class VerticalExpansionStrategy(Enum):
    """
    The strategy to solve the problem of how to expand vertically after new sub-items are added to the layout.
    """
    HeightBalance = enum.auto()
    OrderInsert = enum.auto()
    RandomInsert = enum.auto()


VExpand = VerticalExpansionStrategy


@unique
class OverflowStrategy(Enum):
    """
    The strategy adopted when the column width conflicts with the width of the sub-item.
    """
    Ignore = enum.auto()
    AutoZoom = enum.auto()
    AutoCrop = enum.auto()


Overflow = OverflowStrategy


class QMasonryBoxLayout(QLayout):
    """
    Masonry layout with fixed number of columns
    """
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._horizontalAdaptationStrategy = HorizontalAdaptationStrategy.AutoZoom
        self._verticalExpansionStrategy = VerticalExpansionStrategy.HeightBalance
        self._overflowStrategy = OverflowStrategy.AutoZoom

        self._columnCount: Optional[None, int] = 3
        self._columnWidth: Optional[None, int] = None

        self._horizontalSpacing = 16
        self._verticalSpacing = 16

        self._items: list[QLayoutItem] = []
        self._item_ratios: list[float] = []

    def horizontalAdaptationStrategy(self) -> HorizontalAdaptationStrategy:
        return self._horizontalAdaptationStrategy

    def setHorizontalAdaptationStrategy(self, strategy: HorizontalAdaptationStrategy):
        self._horizontalAdaptationStrategy = strategy

    hAdapt = Property(HorizontalAdaptationStrategy, horizontalAdaptationStrategy, setHorizontalAdaptationStrategy)

    def verticalExpansionStrategy(self) -> VerticalExpansionStrategy:
        return self._verticalExpansionStrategy

    def setVerticalExpansionStrategy(self, strategy: VerticalExpansionStrategy):
        self._verticalExpansionStrategy = strategy

    vExpand = Property(VerticalExpansionStrategy, verticalExpansionStrategy, setVerticalExpansionStrategy)

    def setHorizontalSpacing(self, spacing: int):
        self._horizontalSpacing = spacing

    def horizontalSpacing(self) -> int:
        return self._horizontalSpacing

    hSpace = Property(int, horizontalSpacing, setHorizontalSpacing)

    def setVerticalSpacing(self, spacing: int):
        self._verticalSpacing = spacing

    def verticalSpacing(self) -> int:
        return self._verticalSpacing

    vSpace = Property(int, verticalSpacing, setVerticalSpacing)

    def setColumnCount(self, count: int):
        self._columnCount = count

    def columnCount(self) -> int:
        return self._columnCount

    colCount = Property(int, columnCount, setColumnCount)

    def columnWidth(self) -> int:
        return self._columnWidth

    colWidth = Property(int, columnWidth)

    def calculateColumnWidth(self, rect: QRect, margin: QMargins, spaceX: int):
        columnWidth = (rect.width() - margin.left() - margin.right() - spaceX * (
                self._columnCount - 1)) / self._columnCount
        self._columnWidth = columnWidth

    def _handleOverflow(self, itemWidget: QWidget, itemHeight: int, itemWidth: int):
        if itemWidget.width() != self.columnWidth():
            if self._overflowStrategy == OverflowStrategy.AutoZoom:
                columnHeight = itemHeight * self.columnWidth() // itemWidth
                itemWidget.setFixedSize(self.columnWidth(), columnHeight)
            elif self._overflowStrategy == OverflowStrategy.AutoCrop:
                itemWidget.setFixedWidth(self.columnWidth())
            elif self._overflowStrategy == OverflowStrategy.Ignore:
                pass
            else:
                raise ValueError("Invalid overflow strategy")

    def _handleColumnSelection(self, itemIndex: int, columnTotalHeights: list[int]):
        targetColumnIndex = 0
        if self._verticalExpansionStrategy == VerticalExpansionStrategy.HeightBalance:
            minColumnTotalHeight = columnTotalHeights[0]
            for columnIndex, columnTotalHeight in enumerate(columnTotalHeights):
                if columnTotalHeight < minColumnTotalHeight:
                    targetColumnIndex = columnIndex
        elif self._verticalExpansionStrategy == VerticalExpansionStrategy.OrderInsert:
            targetColumnIndex = itemIndex % self.columnCount()
        elif self._verticalExpansionStrategy == VerticalExpansionStrategy.RandomInsert:
            targetColumnIndex = random.randint(0, self.columnCount() - 1)
        else:
            raise ValueError("Invalid vertical expansion strategy")
        return targetColumnIndex

    def _handlePosition(self, margin: QMargins,
                        spaceX: int, spaceY: int,
                        targetColumnIndex: int,
                        columnTotalHeights: list[int],
                        itemWidth: int, itemHeight: int, itemWidget: QWidget, itemRatio: float):
        if self._horizontalAdaptationStrategy in (
                HorizontalAdaptationStrategy.Spacing, HorizontalAdaptationStrategy.NoAdaption
        ):
            x = margin.left() + self.columnWidth() * (
                    targetColumnIndex + 0.5) + spaceX * targetColumnIndex - itemWidth / 2
            y = margin.top() + columnTotalHeights[targetColumnIndex]
            columnTotalHeights[targetColumnIndex] += itemHeight + spaceY
        elif self._horizontalAdaptationStrategy == HorizontalAdaptationStrategy.AutoZoom:
            x = margin.left() + self.columnWidth() * (
                    targetColumnIndex + 0.5) + spaceX * targetColumnIndex - itemWidth / 2
            y = margin.top() + columnTotalHeights[targetColumnIndex]
            columnHeight = self.columnWidth() * itemRatio
            itemWidget.setFixedSize(self.columnWidth(), int(columnHeight))
            columnTotalHeights[targetColumnIndex] += columnHeight + spaceY
        else:
            raise ValueError("Invalid horizontal adaptation strategy")
        return QRect(x, y, itemWidth, itemHeight)

    def _doLayout(self, rect: QRect):
        margin = self.contentsMargins()
        spaceX = self.horizontalSpacing()
        spaceY = self.verticalSpacing()

        self.calculateColumnWidth(rect, margin, spaceX)

        columnTotalHeights: list[int] = [0 for _ in range(self.columnCount())]

        for itemIndex, (itemRatio, item) in enumerate(zip(self._item_ratios, self._items)):
            itemWidth = item.sizeHint().width()
            itemHeight = item.sizeHint().height()
            itemWidget: QWidget = item.widget()

            self._handleOverflow(itemWidget, itemHeight, itemWidth)

            targetColumnIndex = self._handleColumnSelection(itemIndex, columnTotalHeights)

            itemPosition = self._handlePosition(margin,
                                                spaceX, spaceY,
                                                targetColumnIndex, columnTotalHeights,
                                                itemWidth, itemHeight, itemWidget, itemRatio)

            item.setGeometry(itemPosition)

        return QSize(rect.width(), max(columnTotalHeights))

    def addItem(self, item: QLayoutItem):
        self._items.append(item)
        widget = item.widget()
        self._item_ratios.append(widget.height() / widget.width())

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem:
        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._doLayout(rect)


class QMasonryFlowLayout(QLayout):
    """
    Masonry layout with fixed number of columns
    """
    def __init__(self):
        super().__init__()
        self._horizontalAdaptationStrategy = HorizontalAdaptationStrategy.AutoZoom
        self._verticalExpansionStrategy = VerticalExpansionStrategy.HeightBalance
        self._overflowStrategy = OverflowStrategy.AutoZoom

        self._columnCount: Optional[None, int] = None
        self._columnWidth: Optional[None, int] = 200

        self._horizontalSpacing = 16
        self._verticalSpacing = 16

        self._items: list[QLayoutItem] = []
        self._item_ratios: list[float] = []

    def horizontalAdaptationStrategy(self) -> HorizontalAdaptationStrategy:
        return self._horizontalAdaptationStrategy

    def setHorizontalAdaptationStrategy(self, strategy: HorizontalAdaptationStrategy):
        self._horizontalAdaptationStrategy = strategy

    hAdapt = Property(HorizontalAdaptationStrategy, horizontalAdaptationStrategy, setHorizontalAdaptationStrategy)

    def verticalExpansionStrategy(self) -> VerticalExpansionStrategy:
        return self._verticalExpansionStrategy

    def setVerticalExpansionStrategy(self, strategy: VerticalExpansionStrategy):
        self._verticalExpansionStrategy = strategy

    vExpand = Property(VerticalExpansionStrategy, verticalExpansionStrategy, setVerticalExpansionStrategy)

    def setSpacing(self, spacing: int) -> None:
        self._horizontalSpacing = spacing
        self._verticalSpacing = spacing

    def setHorizontalSpacing(self, spacing: int):
        self._horizontalSpacing = spacing

    def horizontalSpacing(self) -> int:
        return self._horizontalSpacing

    hSpace = Property(int, horizontalSpacing, setHorizontalSpacing)

    def setVerticalSpacing(self, spacing: int):
        self._verticalSpacing = spacing

    def verticalSpacing(self) -> int:
        return self._verticalSpacing

    vSpace = Property(int, verticalSpacing, setVerticalSpacing)

    def columnCount(self) -> int:
        return self._columnCount

    colCount = Property(int, columnCount)

    def setColumnWidth(self, width: int):
        self._columnWidth = width

    def columnWidth(self) -> int:
        return self._columnWidth

    colWidth = Property(int, columnWidth, setColumnWidth)

    def calculateColumnCount(self, rect: QRect, margin: QMargins, spaceX: int):
        columnCount = max(1, (rect.width() - margin.left() - margin.right() + spaceX) // (self._columnWidth + spaceX))
        self._columnCount = columnCount

    def _handleOverflow(self, itemWidget: QWidget, itemHeight: int, itemWidth: int):
        if itemWidget.width() != self.columnWidth():
            if self._overflowStrategy == OverflowStrategy.AutoZoom:
                columnHeight = itemHeight * self.columnWidth() // itemWidth
                itemWidget.setFixedSize(self.columnWidth(), columnHeight)
            elif self._overflowStrategy == OverflowStrategy.AutoCrop:
                itemWidget.setFixedWidth(self.columnWidth())
            elif self._overflowStrategy == OverflowStrategy.Ignore:
                pass
            else:
                raise ValueError("Invalid overflow strategy")

    def _handleColumnSelection(self, itemIndex: int, columnTotalHeights: list[int]):
        targetColumnIndex = 0
        if self._verticalExpansionStrategy == VerticalExpansionStrategy.HeightBalance:
            minColumnTotalHeight = columnTotalHeights[0]
            for columnIndex, columnTotalHeight in enumerate(columnTotalHeights):
                if columnTotalHeight < minColumnTotalHeight:
                    targetColumnIndex = columnIndex
        elif self._verticalExpansionStrategy == VerticalExpansionStrategy.OrderInsert:
            targetColumnIndex = itemIndex % self.columnCount()
        elif self._verticalExpansionStrategy == VerticalExpansionStrategy.RandomInsert:
            targetColumnIndex = random.randint(0, self.columnCount() - 1)
        else:
            raise ValueError("Invalid vertical expansion strategy")
        return targetColumnIndex

    def _handlePosition(self, rect: QRect,
                        margin: QMargins, spaceX: int, spaceY: int,
                        targetColumnIndex: int, columnTotalHeights: list[int],
                        itemWidth: int, itemHeight: int, itemWidget: QWidget, itemRatio: float):
        if self._horizontalAdaptationStrategy == HorizontalAdaptationStrategy.NoAdaption:
            x = margin.left() + self.columnWidth() * (
                    targetColumnIndex + 0.5) + spaceX * targetColumnIndex - itemWidth / 2
            y = margin.top() + columnTotalHeights[targetColumnIndex]
            columnTotalHeights[targetColumnIndex] += itemHeight + spaceY
        elif self._horizontalAdaptationStrategy == HorizontalAdaptationStrategy.Spacing:
            realColumnWidth = (rect.width() - margin.left() - margin.right() - spaceX * (
                    self._columnCount - 1)) / self._columnCount
            x = margin.left() + realColumnWidth * (
                    targetColumnIndex + 0.5) + spaceX * targetColumnIndex - itemWidth / 2
            y = margin.top() + columnTotalHeights[targetColumnIndex]
            columnTotalHeights[targetColumnIndex] += itemHeight + spaceY
        elif self._horizontalAdaptationStrategy == HorizontalAdaptationStrategy.AutoZoom:
            realColumnWidth = (rect.width() - margin.left() - margin.right() - spaceX * (
                    self._columnCount - 1)) / self._columnCount
            x = margin.left() + realColumnWidth * (
                    targetColumnIndex + 0.5) + spaceX * targetColumnIndex - itemWidth / 2
            y = margin.top() + columnTotalHeights[targetColumnIndex]
            columnHeight = realColumnWidth * itemRatio
            itemWidget.setFixedSize(realColumnWidth, columnHeight)
            columnTotalHeights[targetColumnIndex] += columnHeight + spaceY
        else:
            raise ValueError("Invalid horizontal adaptation strategy")
        return QRect(x, y, itemWidth, itemHeight)

    def _doLayout(self, rect: QRect):
        margin = self.contentsMargins()
        spaceX = self.horizontalSpacing()
        spaceY = self.verticalSpacing()

        self.calculateColumnCount(rect, margin, spaceX)

        columnTotalHeights: list[int] = [0 for _ in range(self.columnCount())]

        for itemIndex, (itemRatio, item) in enumerate(zip(self._item_ratios, self._items)):
            itemWidth = item.sizeHint().width()
            itemHeight = item.sizeHint().height()
            itemWidget = item.widget()

            self._handleOverflow(itemWidget, itemHeight, itemWidth)

            targetColumnIndex = self._handleColumnSelection(itemIndex, columnTotalHeights)

            position = self._handlePosition(rect, margin, spaceX, spaceY,
                                            targetColumnIndex, columnTotalHeights,
                                            itemWidth, itemHeight, itemWidget, itemRatio)

            item.setGeometry(position)

        return QSize(rect.width(), max(columnTotalHeights))

    def addItem(self, item: QLayoutItem):
        self._items.append(item)
        widget = item.widget()
        self._item_ratios.append(widget.height() / widget.width())

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem:
        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._doLayout(rect)
