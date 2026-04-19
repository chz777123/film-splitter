from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QCursor

class CropRectItem(QGraphicsRectItem):
    """
    可拖拽且可微调边缘/角落大小的动态裁切框组件
    """
    def __init__(self, rect, frame_index=-1):
        super().__init__(rect)
        self.frame_index = frame_index
        
        # 样式设置：绿色边框，半透明填充
        pen = QPen(QColor(0, 255, 0))
        pen.setWidth(2)
        # 防止缩放时边框变粗
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(0, 255, 0, 40)))
        
        # 允许选中和移动
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        self._is_resizing = False
        self._resize_edges = 0  # 1:Left, 2:Right, 4:Top, 8:Bottom
        self._margin = 20  # 判定为边缘的像素距离 (由于代理图可能很大，容错距离稍大一些)
        
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            # TODO: 限制不能移出场景外
            return value
        return super().itemChange(change, value)
        
    def _get_edges_at_pos(self, pos):
        """判断鼠标位于哪些边缘"""
        rect = self.rect()
        edges = 0
        if abs(pos.x() - rect.left()) < self._margin: edges |= 1
        if abs(pos.x() - rect.right()) < self._margin: edges |= 2
        if abs(pos.y() - rect.top()) < self._margin: edges |= 4
        if abs(pos.y() - rect.bottom()) < self._margin: edges |= 8
        return edges

    def hoverMoveEvent(self, event):
        edges = self._get_edges_at_pos(event.pos())
        if edges == 1 or edges == 2:
            self.setCursor(QCursor(Qt.SizeHorCursor))
        elif edges == 4 or edges == 8:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        elif edges == 5 or edges == 10:  # Top-Left or Bottom-Right
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        elif edges == 6 or edges == 9:  # Top-Right or Bottom-Left
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        else:
            self.setCursor(QCursor(Qt.SizeAllCursor))
            
        super().hoverMoveEvent(event)
        
    def mousePressEvent(self, event):
        edges = self._get_edges_at_pos(event.pos())
        if edges != 0 and event.button() == Qt.LeftButton:
            self._is_resizing = True
            self._resize_edges = edges
            self._press_pos = event.pos()
            self._press_rect = self.rect()
            event.accept()
        else:
            self._is_resizing = False
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self._is_resizing:
            pos = event.pos()
            dx = pos.x() - self._press_pos.x()
            dy = pos.y() - self._press_pos.y()
            
            rect = QRectF(self._press_rect)
            if self._resize_edges & 1: rect.setLeft(rect.left() + dx)
            if self._resize_edges & 2: rect.setRight(rect.right() + dx)
            if self._resize_edges & 4: rect.setTop(rect.top() + dy)
            if self._resize_edges & 8: rect.setBottom(rect.bottom() + dy)
            
            # 限制最小宽高
            if rect.width() >= 10 and rect.height() >= 10:
                self.setRect(rect)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
            # 重新定位 _press_rect 为最新的 rect，以防连续操作
            self._press_rect = self.rect()
        else:
            super().mouseReleaseEvent(event)
