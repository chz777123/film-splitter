from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QImage
from .crop_widget import CropRectItem

class InteractiveCanvas(QGraphicsView):
    """
    渲染 8-bit 代理图的交互画布
    支持鼠标滚轮缩放、中键拖拽平移
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.crop_items = []
        
    def set_image(self, proxy_image):
        """
        加载 8-bit 代理图 (numpy uint8 array)
        """
        if proxy_image is None or proxy_image.size == 0:
            return
            
        h, w = proxy_image.shape
        qimg = QImage(proxy_image.data, w, h, w, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimg)
        
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def render_frames(self, frames):
        """
        根据识别出的坐标数据，在画布上绘制裁切框
        """
        # 清除旧的裁切框
        for item in self.crop_items:
            self.scene.removeItem(item)
        self.crop_items.clear()
        
        # 添加新的裁切框
        for idx, frame in enumerate(frames):
            x = frame["x_start"]
            y = frame["y_start"]
            w = frame["x_end"] - frame["x_start"]
            h = frame["y_end"] - frame["y_start"]
            rect = QRectF(x, y, w, h)
            rect_item = CropRectItem(rect, frame_index=idx)
            self.scene.addItem(rect_item)
            self.crop_items.append(rect_item)

    def get_current_frames(self):
        """
        获取用户微调后的最新裁切框坐标 (代理图坐标系)
        """
        frames = []
        for item in self.crop_items:
            rect = item.sceneBoundingRect()
            frames.append({
                "x_start": int(rect.left()),
                "x_end": int(rect.right()),
                "y_start": int(rect.top()),
                "y_end": int(rect.bottom())
            })
        # 按照 Y 坐标排序
        frames.sort(key=lambda f: f["y_start"])
        return frames

    def wheelEvent(self, event):
        """支持鼠标滚轮缩放"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
